// Loads a language file with Minecraft's own code and renders every string the way the game does.
// Used by `python3 tools/minecraft.py verify`; needs the client jar and its libraries on the classpath.
import java.io.FileInputStream;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import net.minecraft.locale.Language;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.FormattedText;
import net.minecraft.util.FormattedCharSequence;

public class LangCheck {
    public static void main(String[] args) throws Exception {
        Map<String, String> english = new LinkedHashMap<>();
        Map<String, String> corsican = new LinkedHashMap<>();
        try (var in = new FileInputStream(args[0])) { Language.loadFromJson(in, english::put); }
        if (args[1].endsWith(".zip")) {
            // The built pack itself: its metadata through the game's codecs, then its language file.
            try (var zip = new java.util.zip.ZipFile(args[1])) {
                var meta = com.google.gson.JsonParser.parseReader(new java.io.InputStreamReader(
                    zip.getInputStream(zip.getEntry("pack.mcmeta")), java.nio.charset.StandardCharsets.UTF_8)).getAsJsonObject();
                var ops = com.mojang.serialization.JsonOps.INSTANCE;
                var languages = net.minecraft.client.resources.metadata.language.LanguageMetadataSection.CODEC
                    .parse(ops, meta.get("language")).getOrThrow();
                var range = net.minecraft.server.packs.metadata.pack.PackFormat
                    .packCodec(net.minecraft.server.packs.PackType.CLIENT_RESOURCES).codec()
                    .parse(ops, meta.get("pack")).getOrThrow();
                var current = net.minecraft.server.packs.metadata.pack.PackFormat.of(Integer.parseInt(args[2]), Integer.parseInt(args[3]));
                System.out.println("pack.mcmeta: languages " + languages.languages() + ", formats " + range
                    + (range.isValueInRange(current) ? ", accepts " : ", REFUSES ") + current);
                if (!range.isValueInRange(current)) System.exit(1);
                for (var code : languages.languages().keySet()) {
                    var entry = zip.getEntry("assets/minecraft/lang/" + code + ".json");
                    if (entry == null) { System.out.println("no language file for " + code); System.exit(1); }
                    try (var in = zip.getInputStream(entry)) { Language.loadFromJson(in, corsican::put); }
                }
            }
        } else {
            try (var in = new FileInputStream(args[1])) { Language.loadFromJson(in, corsican::put); }
        }
        Map<String, String> active = new LinkedHashMap<>();
        Language.inject(new Language() {
            public String getOrDefault(String key, String fallback) { return active.getOrDefault(key, fallback); }
            public boolean has(String key) { return active.containsKey(key); }
            public boolean isDefaultRightToLeft() { return false; }
            public FormattedCharSequence getVisualOrder(FormattedText text) { return FormattedCharSequence.EMPTY; }
        });
        Pattern argument = Pattern.compile("%(?:(\\d+)\\$)?s");
        Object[] values = new Object[9];
        for (int i = 0; i < values.length; i++) values[i] = "<" + (i + 1) + ">";
        int problems = 0;
        for (var entry : english.entrySet()) {
            String key = entry.getKey();
            if (!corsican.containsKey(key)) { System.out.println("missing\t" + key); problems++; continue; }
            // The arguments English consumes, numbered as Minecraft numbers them.
            java.util.Set<Integer> wanted = new java.util.TreeSet<>();
            Matcher m = argument.matcher(entry.getValue().replace("%%", ""));
            int next = 0;
            while (m.find()) wanted.add(m.group(1) != null ? Integer.parseInt(m.group(1)) : ++next);
            // Minecraft shows the bare template when it cannot format it; English itself does so for a few test keys.
            active.clear(); active.putAll(english);
            String original = Component.translatable(key, values).getString();
            boolean englishRaw = original.equals(entry.getValue()) && entry.getValue().contains("%");
            active.clear(); active.putAll(corsican);
            String rendered = Component.translatable(key, values).getString();
            String template = corsican.get(key);
            boolean raw = !englishRaw && rendered.equals(template) && template.contains("%");
            java.util.Set<Integer> got = new java.util.TreeSet<>();
            Matcher shown = Pattern.compile("<(\\d)>").matcher(rendered);
            while (shown.find()) got.add(Integer.parseInt(shown.group(1)));
            if (raw || !got.equals(wanted)) {
                System.out.println("render\t" + key + "\twanted " + wanted + " got " + got + "\t" + rendered);
                problems++;
            }
        }
        System.out.println("rendered " + english.size() + " keys with Minecraft's code, " + problems + " problems");
        System.exit(problems == 0 ? 0 : 1);
    }
}
