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
        try (var in = new FileInputStream(args[1])) { Language.loadFromJson(in, corsican::put); }
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
