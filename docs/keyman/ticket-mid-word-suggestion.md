# Draft issue for Keyman: a suggestion chosen mid-word leaves the end of the old word

**Draft, not sent.** Prepared for the Corsu maintainer, who decides whether and where to file it
(<https://github.com/keymanapp/keyman/issues>). Nothing here has been posted. Check the tracker for an existing issue
before filing.

## Summary

With the caret inside a word, choosing a suggestion from the banner replaces only the part of the word left of the
caret and adds a space; the part right of the caret stays. `the hou|se is big` + "house" gives `the house se is big`.

## Versions

- Keyman for Android 18.0.254 (stable) and 19.0.309 (beta): the web engine of each official APK
  (`assets/keymanweb-webview.js`, `android-host.js`, `keyboard.html`).
- Keyboard: EuroLatin (SIL), the copy shipped in the APK. Model: `nrc.en.mtnt`, the copy shipped in the APK.
- Suggestion setting: 2, "Predictions with corrections".

## How it was observed

Not on a device. The engine of each APK was run in headless Chrome with a stand-in for the Java bridge
(`window.jsInterface`), called the way `KMKeyboard` calls it: `updateKMText` and `updateKMSelectionRange` for a caret
move, then a tap on the suggestion through the banner's `PredictionContext.accept`. The stand-in applies
`insertText(dn, s, dr)` as `KMKeyboardJSHandler.insertText` does. Harness: `tests/e2e/keyman/harness.mjs` in
<https://github.com/Platykalt/corsu>.

The same result was seen earlier in the Keyman for Android 18.0.254 app on an Android 14 emulator, with a Corsican
model: `Dopu ell|a vene` + "ellu" gave `Dopu ellu a vene`.

## Steps (on a device)

1. Keyman for Android, English, default keyboard and dictionary, "Predictions with corrections".
2. In Keyman's text field, type `the house is big`.
3. Move the caret between `hou` and `se`.
4. Tap "house" in the banner.

## Results in the engine (both versions identical)

| Text, caret | Tapped | Result | Expected |
| --- | --- | --- | --- |
| `the hou\|se is big` | house | `the house se is big` | `the house is big` |
| `the hou\|se.` | house | `the house se.` | `the house.` |
| `the [house] is big` (word selected) | first suggestion, "The" | `the The is big` | a suggestion for the selected word, or none |

In the third row the banner, with a word selected mid-sentence, shows the suggestions of an empty context with a
capital (The, To, And...), and tapping one replaces the selection with it.

## Where it comes from

- `web/src/engine/predictive-text/worker-thread/src/main/predict-helpers.ts`, `finalizeSuggestions`: under the
  comment "If we're mid-word, delete its original post-caret text.", the `caretSplitsToken` branch only appends
  `punctuation.insertAfterWord`; the suggestion's transform gets no `deleteRight`. (19.0 sets `appendedTransform`
  instead, with the same effect.)
- Keyman for Android applies `deleteRight`: `KMKeyboardJSHandler.insertText` deletes `dr` characters after the caret.
  A model that sets `deleteRight` on its suggestions gets the expected result on Android (checked in the 18.0.254 and
  19.0.309 engines).
- Keyman for iPhone and iPad does not: `KeymanWebViewController` reads `dr` and drops it ("Use it when we're ready to
  implement that"), on `stable-18.0`, `beta` and `master`. The engine's own text store does apply `deleteRight`
  (`TextStore.apply`), so on iOS the engine's context and the app's text can differ after such an edit.

## Related, smaller

- **A space is added before punctuation already written after the word.** `finalizeSuggestions` appends
  `punctuation.insertAfterWord` unless `context.right` starts with it; when the word (or the end of the word, in the
  mid-word case) is directly followed by `.`, `,`, `)`, `»`, a hyphen or a line break, the space lands before it:
  `Aiacc|.` + "Aiacciu" gives `Aiacciu .`, `Aiacc|iu.` gives `Aiacciu .` once the end of the word is deleted,
  `Port|o-Vecchio` + "Portu" gives `Portu -Vecchio`. Seen in the 18.0.254 and 19.0.309 engines and in the 18.0.254
  app (Android 14 emulator). Suggested change: do not append it when the text after the token starts with
  punctuation or any whitespace (not only `insertAfterWord`). Corsu works around it (below).
- The reversion offered after accepting (`acceptSuggestion` in `model-compositor.ts`) restores only the left part:
  after a mid-word choice that deleted text right of the caret, backspace then the quoted word gives
  `Eccu a ca|di Petru.` from `Eccu a ca|sa di Petru.`.
- **Keyman 18.0: punctuation typed after a tapped suggestion** keeps the appended space (`casa .`). Keyman 19.0.309
  removes it (`doPredictiveAutoBreaking`), seen in the 19.0.309 app on an Android 14 emulator, in Keyman's own field
  and as the system keyboard: `casa` tapped, then `.`, space, `Do` gives `A casa. Do`. (In a headless page with a
  stand-in bridge that does not echo text changes back, the space typed after the `.` also removed the `.`: a limit
  of that stand-in, not reproduced in the app; mentioned only in case another host behaves like it.)
- **Words outside the lexicon cannot be recognised by the model.** The correction search (18.0.254 and 19.0.309)
  only follows paths of the lexicon, and `predict` is only called with those roots, so a model cannot tell the
  engine that a typed word it does not list is valid (an elided form of a known word, `l'abitanti`, is replaced by
  `abitanti` with auto-correction on). In 19.0.309 the outcome also depends on time: in a headless page the same
  typing was kept in five runs of six (the search ran out of time and offered nothing) and replaced in one. A hook
  for the model to accept a word as known would help languages with elision or clitics.

## What Corsu does meanwhile

Corsu's models (Keyman packages `platykalt.co.corsu*`, `keyboard/whole-word.js` in the Corsu repository):

- set `deleteRight` themselves on Android only, where the app applies it; on iOS they leave suggestions as they are.
  If Keyman fixes this in the engine, that part must go, or the end of the word would be deleted twice;
- expose `punctuation` through a getter that returns an empty `insertAfterWord` while the current prediction's
  context has punctuation or a line break right after the word (at the end of the word on every platform, inside it
  on Android). This relies on `finalizeSuggestions` reading the model's punctuation for each set of suggestions,
  after calling the model's `predict` for the same context (18.0.254 and 19.0.309). If the engine stops adding the
  space itself, the getter becomes a no-op.
