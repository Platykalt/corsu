// Corsu: what a chosen suggestion does to the text around the caret (Keyman lexical model wrapper).
//
// tools/build_keyboard.py wraps the compiled trie model with this function. Four adjustments, each for a case
// where Keyman's engine (18.0 and 19.0) changes text the user did not ask to change:
//
// 1. Whole word, caret inside it (Keyman for Android only). The engine replaces only the part of a word left of
//    the caret when a suggestion is chosen mid-word, and adds a space: "ca|sa" + "casa" gave "casa sa". Each
//    suggestion's transform also gets deleteRight, a field of Keyman's lexical-model Transform, for the rest of
//    the word right of the caret and the space after it. The model's own word breaker decides what "the rest of
//    the word" is, as the engine does to find the word being typed. Only where the app applies deleteRight:
//    Keyman for Android does (KMKeyboardJSHandler.insertText); Keyman for iPhone and iPad 18.0 and 19.0 read the
//    value and ignore it (KeymanWebViewController), so elsewhere the end of the word is left as it is.
// 2. No space before the punctuation already written after the word. The engine adds a space after a chosen
//    word (the model's punctuation.insertAfterWord) unless the text right of the caret starts with a space:
//    "Aiacc|." + "Aiacciu" gave "Aiacciu .". When the word (with its end, on Android) is directly followed by a
//    punctuation mark or a line break, the model's insertAfterWord is empty for that prediction, and the spacing
//    already in the text stays as written. The engine reads the model's punctuation for each set of
//    suggestions (finalizeSuggestions), after asking the model for them. On iPhone, only when the caret is at
//    the end of the word: there the end of a word cut by the caret stays, and the space keeps it apart.
//    A punctuation mark typed after a chosen suggestion is the keyboard's input, not the model's: Keyman 19
//    removes the space then; Keyman 18 does not, and no model can.
// 3. An elided word is known when its second part is: "L'ADECEC", "d'abitanti". The word list holds the
//    frequent elided forms as words (l'annu, ch'ella); for the others the model offers the word as typed, which
//    is how the engine recognises a known word, so auto-correction keeps it ("L'ADECEC" became "ADECEC").
// 4. A typographic apostrophe stays. The word list writes elisions with ' (U+0027); when the word being
//    replaced is written with ’ (U+2019), the suggestions use ’ too: "l’is" + "l'isula" gives "l’isula".
//
// Plain ES5: it runs in the engine's prediction worker.
function corsuWholeWord(model) {
  var predict = model.predict;
  var android = typeof navigator !== 'undefined' && /Android/.test(navigator.userAgent || '');
  // What, written right after a word, belongs with it: closing punctuation, a hyphen or dash, a slash, a line
  // break or a no-break space. (A plain space is the engine's own case; an apostrophe is part of the word.)
  var attached = /^[.,;:!?\u2026)\]}\u00bb\u203a\u201d"%\-\u2013\u2014\/\t\n\r\u00a0\u202f\u2009]/;
  var punctuation = model.punctuation;
  var noSpace = false;
  Object.defineProperty(model, 'punctuation', {
    configurable: true,
    enumerable: true,
    get: function() {
      if (!noSpace) {
        return punctuation;
      }
      var copy = {};
      for (var key in punctuation || {}) {
        copy[key] = punctuation[key];
      }
      copy.insertAfterWord = '';
      return copy;
    },
    set: function(value) {
      punctuation = value;
    }
  });
  function codePoints(text) {
    return Array.from(text).length;
  }
  // The model's entry for a word, from its lexicon: { text, p } or null. Several entries can share the word's search
  // key (Corti, corti); the one written as the word is preferred.
  function known(lexicon, word) {
    var node = lexicon.traverseFromRoot().child(lexicon.toKey(word));
    var entries = (node && node.entries) || [];
    for (var i = 0; i < entries.length; i++) {
      if (entries[i].text === word) {
        return entries[i];
      }
    }
    return entries.length ? entries[0] : null;
  }
  model.predict = function(transform, context) {
    var distribution = predict.call(this, transform, context);
    var right = (context && context.right) || '';
    var before = Array.from((context && context.left) || '');
    var left = before.slice(0, Math.max(0, before.length - (transform.deleteLeft || 0))).join('')
      + (transform.insert || '');
    var breakWords = this.wordbreaker || this.breakWords;
    var leftWords = breakWords(left);
    var last = leftWords.length ? leftWords[leftWords.length - 1] : null;
    // The caret is right after a word (or a part of one).
    var atWord = !!last && last.end === left.length;
    var rest = '';
    if (atWord && right) {
      var after = breakWords(right);
      // The caret is inside a word when the word before it and the one after it are one word together.
      if (after.length && after[0].start === 0 && breakWords(last.text + after[0].text).length === 1) {
        rest = after[0].text;
      }
    }
    var next = right.slice(rest.length);
    noSpace = atWord && attached.test(next) && (!rest || android);
    var i, change;
    // An elided word whose second part the model knows ("L'ADECEC", "d'abitanti") is a word, not a typo: it is
    // offered, with the second part as the word list writes it, so that the engine finds the typed word in the
    // model (casing applied) and auto-correction keeps it. Keyman 18 hands the model the root in lowercase.
    var elision = atWord ? /^([^'\u2019\s\d.,;:!?]{1,5})(['\u2019])(.+)$/.exec(last.text) : null;
    var insert = transform.insert || '';
    // A second part of one or two letters (un'a, ch'el) is too often a word being typed: it is left to the engine.
    var tail = elision && codePoints(elision[3]) >= 3 && this.traverseFromRoot
      && last.text.slice(-insert.length || last.text.length) === insert ? known(this, elision[3]) : null;
    if (tail && !known(this, last.text)) {
      var word = elision[1] + elision[2] + tail.text;
      distribution.push({
        sample: {
          transform: { insert: word, deleteLeft: (transform.deleteLeft || 0) + codePoints(last.text) - codePoints(insert) },
          displayAs: word
        },
        p: tail.p
      });
    }
    // The word as written in the text: Keyman 19 hands the model a corrected root, written with '.
    var written = (context && context.left) || '';
    var typed = breakWords(written);
    typed = typed.length && typed[typed.length - 1].end === written.length ? typed[typed.length - 1].text : '';
    if (atWord && (last.text + typed).indexOf('\u2019') >= 0) {
      for (i = 0; i < distribution.length; i++) {
        change = distribution[i].sample;
        change.transform.insert = change.transform.insert.replace(/'/g, '\u2019');
        if (change.displayAs) {
          change.displayAs = change.displayAs.replace(/'/g, '\u2019');
        }
      }
    }
    if (rest && android) {
      // Keyman adds a space after a word chosen mid-word: the space already there goes, not doubled.
      var deleteRight = codePoints(rest) + (next.charAt(0) === ' ' ? 1 : 0);
      for (i = 0; i < distribution.length; i++) {
        change = distribution[i].sample.transform;
        change.deleteRight = (change.deleteRight || 0) + deleteRight;
      }
    }
    return distribution;
  };
  return model;
}
