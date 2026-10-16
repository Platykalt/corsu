# Testing the Corsican pack in Minecraft Java 26.3

[Français](../../docs/fr/minecraft-tester.md)

Nobody has seen this translation in a running game yet ([STATUS.md](STATUS.md)). If you own Minecraft: Java Edition,
one hour going through the screens below is the most useful help there is. You do not need to speak Corsican to spot
text that overflows a button or English left behind; if you do speak it, also look at the wording.

## 1. Install

1. Use **Minecraft: Java Edition 26.3** (in the launcher: Installations → New → version 26.3). Another version works
   with a warning, but texts added or changed by Mojang since then will be in English.
2. Get `corsu-minecraft-java-26.3.zip` from the [latest release](https://github.com/Platykalt/corsu/releases/latest),
   or build it: `python3 tools/minecraft.py build`. Do not unzip it. (The Corsu installer can also do steps 3–4 for you.)
3. In the game: **Options… → Resource Packs… → Open Pack Folder**, drop the zip there, go back, move the pack to the
   right-hand column with its arrow, then **Done**.
4. **Options… → Language…**, pick **Corsu (Corsica)**, then **Done**.

To test your own corrections live, unzip the pack into a folder in `resourcepacks/`, edit
`assets/minecraft/lang/co_fr.json` there, and press **F3 + T** in game to reload resources.

## 2. Screens to check

Take a screenshot (F2) of anything wrong; screenshots are in `.minecraft/screenshots`.

1. **Title screen**: every button, the language button tooltip, the copyright line.
2. **Options** and each sub-screen: Skin Customization, Music & Sounds, Video Settings (sliders: *Render Distance*,
   *Simulation Distance*, *GUI Scale*…), Controls → Mouse Settings and Key Binds (scroll the whole list), Chat
   Settings, Accessibility Settings, Online, Telemetry Data, Credits & Attribution. Hover each option to read its tooltip.
3. **Language list**: Corsu (Corsica) appears and is sorted sensibly; nothing else changed.
4. **Create New World**: the Game, World and More tabs; cycle *Game Mode* (Survival, Hardcore, Creative) and
   *Difficulty* and read the descriptions; the *Seed* field and its hint; *Game Rules* (every category);
   *Data Packs* and *Experiments*.
5. **Inventory and creative tabs**: open each creative tab, hover many items (tools, enchanted books, potions and
   tipped arrows, spawn eggs, coloured wool/concrete, banners, armour trims, pottery sherds, music discs). Press
   F3 + H for advanced tooltips once.
6. **Crafting**: crafting table and recipe book (search box, filter button), furnace, anvil (rename), enchanting
   table, grindstone, smithing table, stonecutter, loom, brewing stand, a villager's trading screen (job level names).
7. **F3 debug screen**, and F3 + Q (list of debug keys).
8. **Death screen**: die once (and in a Hardcore world if you can), read the death message in chat.
9. **Chat and commands**: type `/` and browse suggestions; try commands that fail on purpose, e.g.
   `/give @s nothing`, `/give @s stone 99999`, `/tp nobody`, `/gamerule`, `/seed`, `/time set day`,
   `/effect give @s minecraft:speed`, `/locate structure village_plains`.
10. **Advancements screen** (L): every tab, titles and descriptions; trigger one advancement to see its toast.
11. **Subtitles**: Music & Sounds → *Closed Captions* ON, then walk among animals, open doors and chests, go near
    water, lava and a cave.
12. **Realms**: the *Minecraft Realms* button from the title screen (the intro and buy screens show without a
    subscription), plus **Multiplayer**: server list, Add Server, Direct Connection, and the pause menu's
    *Open to LAN*.

## 3. What to look for

- **Overflow**: Corsican is often longer than English. Text that runs past a button, slider or tooltip edge, is cut
  with "…", or overlaps something else. Note the screen and the window size / GUI Scale.
- **English left over**, or a raw key such as `item.minecraft.foo`, or a visible `%s` / `%1$s`.
- **Wrong sense**: a word that translates the English literally but means something else in the game
  (e.g. a mob name that reads like an object, a setting that says the opposite of what it does).
- **Grammar**: gender and number (*a lana rossa*, *i blocchi rossi*), elision (*l'ogettu*, *d'un*), negation
  (*ùn … micca*).
- **Inconsistency**: one thing with two names on different screens.
- Words you, as a speaker, would never use. The list of uncertain terms is in [review.md](review.md) and
  [decisions.md](decisions.md): your opinion on those is especially welcome.

## 4. Find the key of a text

Each text has a key in [co_fr.json](co_fr.json) (one line per key, e.g. `"gui.done": "Fattu"`):

- On GitHub, open [co_fr.json](https://github.com/Platykalt/corsu/blob/main/minecraft/java/co_fr.json) (or its
  **Raw** view) and search the exact Corsican text you saw with your browser's Ctrl+F.
  If it contains a name or a number, search a fixed part of it (the rest is a `%s`).
- If the same text has several keys, switch the game to English, note the English text and search it in Mojang's
  `en_us.json` (`python3 tools/minecraft.py fetch 26.3` puts it in `~/.cache/corsu/minecraft/26.3/`); the key next
  to it is the one to report.
- Not finding the key is fine: the screen and the text you saw are enough.

## 5. Report

Open an issue with the **Translation** template:
<https://github.com/Platykalt/corsu/issues/new?template=translation.yml>

- **Text you saw**: copy it exactly.
- **Where**: "Minecraft Java 26.3" + the screen (e.g. *Options → Video Settings, Render Distance slider*).
- **Corsican you suggest**: optional.
- **Key**: if you found it.
- **Notes**: what is wrong (overflow, sense, English left…), and attach the screenshot.

One issue per problem is easiest to follow; for a whole screen that looks fine, a short "screen X checked, nothing
to report" comment is useful too: it lets us mark those keys `verified in game` in [inventory.tsv](inventory.tsv).
