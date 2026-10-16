// Loads a Corsu pack with the classes of an official Minecraft client jar of ANY version from 1.6.1, obfuscated
// or not, and renders every text the way that version's client does. Used by `python3 tools/mcversions.py verify`.
//
// The jar's class names are obfuscated and change with every version, so the Python side finds candidate classes by
// the string constants they hold (the loader's numeric-format pattern "%(\d+\$)?[\d\.]*[df]", "Format error: ",
// "lang/%s.json", "bidirectional", "pack_format") and this program picks among them by method signatures:
//   - the language loader: an instance method (InputStream) -> void filling a Map (1.6 to 1.13: the client Locale,
//     whose (String, Object[]) -> String method formats a text), or a static (InputStream, BiConsumer) (1.14 and
//     later: Language.loadFromJson);
//   - for the static style, the client language (private constructor (Map, boolean)) put into I18n by its static
//     setter, and I18n's static (String, Object...) -> String, the method the game calls for screens;
//   - the metadata readers of the pack.mcmeta sections "language" and "pack" (a Gson JsonDeserializer, a
//     metadata section serializer with a (JsonObject) method, or a static Codec / MapCodec read with JsonOps).
// Nothing is reimplemented: loading, the game's own normalisation of %d / %.1f into %s, and String.format with the
// game's fallback ("Format error: ...") are the jar's code. Text components (chat, advancements…) use another
// renderer whose rule is checked in Python; for 26.x, tools/minecraft/LangCheck.java runs that renderer too.
//
// Arguments: english.json (key -> raw English text) english-game-file (the same English in the version's own
// format) pack.zip lang-entry expected-code expected-pack-format loaders i18ns clientLanguages languageMetas packMetas
// (the last five: comma-separated class names, or "-"). Exit 0: no problem; 1: problems; 2: the engine was not found.
// In a package of its own: old jars are signed, and an unsigned class in their (default) package cannot load beside them.
package corsu;

import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Collection;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.TreeSet;
import java.util.function.BiConsumer;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.zip.ZipFile;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

public class LegacyFormatCheck {
    interface Engine { String format(String key, Object[] args) throws Exception; Map<String, String> table(); String describe(); }

    static List<Class<?>> classes(String list) {
        List<Class<?>> found = new ArrayList<>();
        if (list.equals("-")) return found;
        for (String name : list.split(",")) {
            try { found.add(Class.forName(name, false, LegacyFormatCheck.class.getClassLoader())); }
            catch (Throwable error) { System.out.println("note\tcannot load " + name + ": " + error); }
        }
        return found;
    }

    static Method staticLoader(Class<?> type) {
        for (Method m : type.getDeclaredMethods()) {
            Class<?>[] p = m.getParameterTypes();
            if (Modifier.isStatic(m.getModifiers()) && p.length == 2 && p[0] == InputStream.class && p[1] == BiConsumer.class) return m;
        }
        return null;
    }

    static Method instanceMethod(Class<?> type, Class<?> result, Class<?>... parameters) {
        for (Method m : type.getDeclaredMethods())
            if (!Modifier.isStatic(m.getModifiers()) && m.getReturnType() == result && java.util.Arrays.equals(m.getParameterTypes(), parameters)) return m;
        return null;
    }

    static Field mapField(Class<?> type) {
        for (Field f : type.getDeclaredFields()) if (!Modifier.isStatic(f.getModifiers()) && Map.class.isAssignableFrom(f.getType())) return f;
        return null;
    }

    // Choose how this version loads and formats, then load `data` with it.
    static Engine engine(List<Class<?>> loaders, List<Class<?>> i18ns, List<Class<?>> clients, byte[] data) throws Exception {
        for (Class<?> loader : loaders) {
            Method read = instanceMethod(loader, void.class, InputStream.class);
            Method format = instanceMethod(loader, String.class, String.class, Object[].class);
            Field map = mapField(loader);
            if (read != null && format != null && map != null) {
                Constructor<?> constructor = loader.getDeclaredConstructor();
                constructor.setAccessible(true);
                Object locale = constructor.newInstance();
                read.setAccessible(true); format.setAccessible(true); map.setAccessible(true);
                read.invoke(locale, new ByteArrayInputStream(data));
                @SuppressWarnings("unchecked") Map<String, String> table = (Map<String, String>) map.get(locale);
                // Up to 1.12 the Locale also decides whether the game switches to its Unicode font (more than 10 % of
                // characters above U+00FF): reported, as it changes how every text looks.
                for (Method m : loader.getDeclaredMethods())
                    if (!Modifier.isStatic(m.getModifiers()) && m.getReturnType() == boolean.class && m.getParameterCount() == 0) {
                        m.setAccessible(true);
                        System.out.println("note\tUnicode font forced by this file: " + m.invoke(locale));
                    }
                return new Engine() {
                    public String format(String key, Object[] args) throws Exception { return (String) format.invoke(locale, key, args); }
                    public Map<String, String> table() { return table; }
                    public String describe() { return loader.getName() + "." + read.getName() + "(InputStream) and ." + format.getName() + "(String, Object[])"; }
                };
            }
            Method load = staticLoader(loader);
            if (load == null) continue;
            load.setAccessible(true);
            Map<String, String> table = new LinkedHashMap<>();
            BiConsumer<String, String> put = table::put;
            load.invoke(null, new ByteArrayInputStream(data), put);
            for (Class<?> client : clients) {
                if (!loader.isAssignableFrom(client)) continue;
                Constructor<?> make = null;
                for (Constructor<?> c : client.getDeclaredConstructors())
                    if (c.getParameterCount() == 2 && c.getParameterTypes()[0] == Map.class && c.getParameterTypes()[1] == boolean.class) make = c;
                if (make == null) continue;
                make.setAccessible(true);
                Object language = make.newInstance(table, false);
                for (Class<?> i18n : i18ns) {
                    Method set = null, get = null;
                    for (Method m : i18n.getDeclaredMethods()) {
                        if (!Modifier.isStatic(m.getModifiers())) continue;
                        Class<?>[] p = m.getParameterTypes();
                        if (p.length == 1 && p[0] == loader && m.getReturnType() == void.class) set = m;
                        if (p.length == 2 && p[0] == String.class && p[1] == Object[].class && m.getReturnType() == String.class) get = m;
                    }
                    // 26.2 and later: I18n reads Language.getInstance(), set by Language's own static setter (inject).
                    if (set == null)
                        for (Method m : loader.getDeclaredMethods())
                            if (Modifier.isStatic(m.getModifiers()) && m.getParameterCount() == 1 && m.getParameterTypes()[0] == loader && m.getReturnType() == void.class) set = m;
                    if (set == null || get == null) continue;
                    set.setAccessible(true); get.setAccessible(true);
                    final Method setter = set, getter = get;
                    return new Engine() {
                        public String format(String key, Object[] args) throws Exception { setter.invoke(null, language); return (String) getter.invoke(null, key, (Object) args); }
                        public Map<String, String> table() { return table; }
                        public String describe() { return loader.getName() + "." + load.getName() + "(InputStream, BiConsumer), " + client.getName() + "(Map, boolean), " + i18n.getName() + "." + getter.getName() + "(String, Object...)"; }
                    };
                }
            }
        }
        return null;
    }

    // Arguments typed as the English text uses them: %d gets an Integer, %f a Double, anything else a String.
    static final Pattern SPEC = Pattern.compile("%(?:(\\d+)\\$)?[-#+ 0,(]*\\d*(?:\\.\\d+)?([a-zA-Z%])");
    static Object[] arguments(String english) {
        Object[] values = new Object[9];
        for (int i = 0; i < values.length; i++) values[i] = "<" + (i + 1) + ">";
        Matcher m = SPEC.matcher(english);
        int next = 0;
        while (m.find()) {
            char kind = m.group(2).charAt(0);
            if (kind == '%' || kind == 'n') continue;
            int index = m.group(1) != null ? Integer.parseInt(m.group(1)) : ++next;
            if (index < 1 || index > 9) continue;
            if (kind == 'd') values[index - 1] = 1000 + index;
            else if (kind == 'f') values[index - 1] = 2000 + index + 0.5;
        }
        return values;
    }

    static final Pattern SHOWN = Pattern.compile("<(\\d)>|(?<![\\d.])100(\\d)(?![\\d.])|(?<![\\d.])200(\\d)\\.5");
    static Set<Integer> shown(String text) {
        Set<Integer> found = new TreeSet<>();
        Matcher m = SHOWN.matcher(text);
        while (m.find()) found.add(Integer.parseInt(m.group(1) != null ? m.group(1) : m.group(2) != null ? m.group(2) : m.group(3)));
        return found;
    }

    // ---- pack.mcmeta sections, read by the version's own metadata classes
    static Object decode(Class<?> type, JsonElement json) throws Exception {
        for (Field f : type.getDeclaredFields()) {
            if (!Modifier.isStatic(f.getModifiers())) continue;
            String kind = f.getType().getName();
            if (kind.equals("com.mojang.serialization.Codec") || kind.equals("com.mojang.serialization.MapCodec")) {
                f.setAccessible(true);
                Object codec = f.get(null);
                if (kind.endsWith("MapCodec")) codec = codec.getClass().getMethod("codec").invoke(codec);
                Class<?> ops = Class.forName("com.mojang.serialization.JsonOps");
                Object instance = ops.getField("INSTANCE").get(null);
                Method parse = Class.forName("com.mojang.serialization.Decoder").getMethod("parse", Class.forName("com.mojang.serialization.DynamicOps"), Object.class);
                Object result = parse.invoke(codec, instance, json);
                Optional<?> value = (Optional<?>) result.getClass().getMethod("result").invoke(result);
                if (!value.isPresent()) throw new IllegalArgumentException(String.valueOf(result));
                return value.get();
            }
        }
        Object reader = null;
        for (Constructor<?> c : type.getDeclaredConstructors()) if (c.getParameterCount() == 0) { c.setAccessible(true); reader = c.newInstance(); }
        if (reader == null) throw new IllegalStateException("no reader in " + type.getName());
        for (Method m : type.getMethods()) {
            Class<?>[] p = m.getParameterTypes();
            // The context would turn "description" into a text component with another class: it gives an empty
            // stand-in here, so only the other fields (pack_format, the languages) are read by the game's code.
            if (m.getName().equals("deserialize") && p.length == 3) return m.invoke(reader, json, null, new com.google.gson.JsonDeserializationContext() {
                @SuppressWarnings("unchecked")
                public <T> T deserialize(JsonElement element, java.lang.reflect.Type type) {
                    if (!(type instanceof Class) || !((Class<?>) type).isInterface()) return null;
                    return (T) java.lang.reflect.Proxy.newProxyInstance(LegacyFormatCheck.class.getClassLoader(), new Class<?>[] {(Class<?>) type},
                        (proxy, method, arguments) -> method.getReturnType() == boolean.class ? false : method.getReturnType() == int.class ? 0 : null);
                }
            });
        }
        for (Method m : type.getMethods())
            if (m.getParameterCount() == 1 && m.getParameterTypes()[0] == JsonObject.class && m.getReturnType() != JsonObject.class)
                return m.invoke(reader, json.getAsJsonObject());
        throw new IllegalStateException("no reading method in " + type.getName());
    }

    // Every string, number and boolean reachable from a decoded section (obfuscated fields, records, collections).
    static void dump(Object value, List<Object> out, int depth) throws Exception {
        if (value == null || depth > 5) return;
        if (value instanceof String || value instanceof Number || value instanceof Boolean) { out.add(value); return; }
        if (value instanceof Optional) { dump(((Optional<?>) value).orElse(null), out, depth + 1); return; }
        if (value instanceof Collection) { for (Object o : (Collection<?>) value) dump(o, out, depth + 1); return; }
        if (value instanceof Map) { for (Map.Entry<?, ?> e : ((Map<?, ?>) value).entrySet()) { dump(e.getKey(), out, depth + 1); dump(e.getValue(), out, depth + 1); } return; }
        if (value.getClass().getName().startsWith("java.")) { out.add(value.toString()); return; }
        for (Class<?> c = value.getClass(); c != null && c != Object.class; c = c.getSuperclass()) {
            for (Field f : c.getDeclaredFields()) {
                if (Modifier.isStatic(f.getModifiers())) continue;
                try { f.setAccessible(true); dump(f.get(value), out, depth + 1); } catch (RuntimeException ignored) { }
            }
        }
    }

    static byte[] read(InputStream in) throws Exception {
        ByteArrayOutputStream out = new ByteArrayOutputStream();
        byte[] buffer = new byte[65536];
        for (int n; (n = in.read(buffer)) > 0; ) out.write(buffer, 0, n);
        return out.toByteArray();
    }

    @SuppressWarnings("deprecation")
    public static void main(String[] args) throws Exception {
        Locale.setDefault(Locale.ROOT);
        JsonObject englishJson = new JsonParser().parse(new String(Files.readAllBytes(Paths.get(args[0])), StandardCharsets.UTF_8)).getAsJsonObject();
        Map<String, String> english = new LinkedHashMap<>();
        for (Map.Entry<String, JsonElement> e : englishJson.entrySet()) english.put(e.getKey(), e.getValue().getAsString());
        byte[] englishGame = Files.readAllBytes(Paths.get(args[1]));
        byte[] corsicanGame, mcmeta;
        try (ZipFile zip = new ZipFile(args[2])) {
            if (zip.getEntry(args[3]) == null) { System.out.println("problem\tno " + args[3] + " in the pack"); System.exit(1); }
            try (InputStream in = zip.getInputStream(zip.getEntry(args[3]))) { corsicanGame = read(in); }
            try (InputStream in = zip.getInputStream(zip.getEntry("pack.mcmeta"))) { mcmeta = read(in); }
        }
        String code = args[4];
        int packFormat = Integer.parseInt(args[5]);
        List<Class<?>> loaders = classes(args[6]), i18ns = classes(args[7]), clients = classes(args[8]);
        int problems = 0;

        JsonObject meta = new JsonParser().parse(new InputStreamReader(new ByteArrayInputStream(mcmeta), StandardCharsets.UTF_8)).getAsJsonObject();
        String[][] sections = {{"language", args[9]}, {"pack", args[10]}};
        for (String[] section : sections) {
            List<Class<?>> readers = classes(section[1]);
            boolean read = false;
            for (Class<?> reader : readers) {
                try {
                    List<Object> values = new ArrayList<>();
                    Object decoded;
                    try { decoded = decode(reader, meta.get(section[0])); }
                    catch (Throwable whole) {
                        // 1.20 and later: the reader found is the codec of one language (name, region, bidirectional);
                        // the section is a map from code to language, read entry by entry here.
                        if (!section[0].equals("language") || reader.getDeclaredFields().length == 0) throw whole;
                        Map<String, Object> each = new LinkedHashMap<>();
                        for (Map.Entry<String, JsonElement> e : meta.getAsJsonObject("language").entrySet()) each.put(e.getKey(), decode(reader, e.getValue()));
                        decoded = each;
                        System.out.println("note\tlanguage entries read one by one with " + reader.getName() + " (the code itself is checked in Python)");
                    }
                    dump(decoded, values, 0);
                    boolean ok = section[0].equals("language")
                        ? values.contains(code) && values.contains("Corsu") && values.contains("Corsica")
                        : values.contains(packFormat);
                    System.out.println("metadata\t" + section[0] + "\t" + reader.getName() + "\t" + (ok ? "accepted" : "WRONG") + "\t" + values);
                    if (!ok) problems++;
                    read = true;
                    break;
                } catch (Throwable error) {
                    Throwable cause = error;
                    while (cause.getCause() != null && cause != cause.getCause()) cause = cause.getCause();
                    System.out.println("metadata\t" + section[0] + "\t" + reader.getName() + "\trefused or unreadable: " + cause);
                }
            }
            if (!read) System.out.println("metadata\t" + section[0] + "\tnot read by the game's code (no usable reader)");
        }

        Engine en, co;
        try {
            en = engine(loaders, i18ns, clients, englishGame);
            co = engine(loaders, i18ns, clients, corsicanGame);
        } catch (Throwable error) {
            System.out.println("engine\tfailed: " + error);
            error.printStackTrace(System.out);
            System.exit(2);
            return;
        }
        if (en == null || co == null) { System.out.println("engine\tnot found"); System.exit(2); }
        System.out.println("engine\t" + co.describe());
        int checked = 0, extra = 0, englishRaw = 0;
        for (String key : co.table().keySet()) {
            if (!english.containsKey(key)) { System.out.println("extra\t" + key); extra++; problems++; }
        }
        for (Map.Entry<String, String> entry : english.entrySet()) {
            String key = entry.getKey();
            if (!co.table().containsKey(key)) continue;
            checked++;
            Object[] values = arguments(entry.getValue());
            String original = en.format(key, values), rendered = co.format(key, values);
            if (original.startsWith("Format error: ")) { englishRaw++; continue; }
            if (rendered.startsWith("Format error: ") || !shown(original).equals(shown(rendered))) {
                System.out.println("render\t" + key + "\twanted " + shown(original) + " got " + shown(rendered) + "\t" + rendered);
                problems++;
            }
        }
        System.out.println("rendered " + checked + " Corsican texts with the game's own loader and formatter (" + englishRaw
            + " skipped: the English itself does not format), " + extra + " unknown keys, " + problems + " problems");
        System.exit(problems == 0 ? 0 : 1);
    }
}
