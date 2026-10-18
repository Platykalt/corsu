// Corsu: a suggestion chosen with the caret inside a word replaces the whole word (Keyman for Android).
//
// tools/build_keyboard.py wraps the compiled trie model with this function. Keyman's engine (18.0 and 19.0)
// replaces only the part of a word left of the caret when a suggestion is chosen mid-word, and adds a space:
// "ca|sa" + "casa" gave "casa sa". Each suggestion's transform also gets deleteRight, a field of Keyman's
// lexical-model Transform, for the rest of the word right of the caret and the space after it. The model's
// own word breaker decides what "the rest of the word" is, as the engine does to find the word being typed.
//
// Only where the app applies deleteRight: Keyman for Android does (KMKeyboardJSHandler.insertText); Keyman
// for iPhone and iPad 18.0 and 19.0 read the value and ignore it (KeymanWebViewController), so elsewhere the
// suggestions are left as they are. Plain ES5: it runs in the engine's prediction worker.
function corsuWholeWord(model) {
  var predict = model.predict;
  var android = typeof navigator !== 'undefined' && /Android/.test(navigator.userAgent || '');
  if (!android) {
    return model;
  }
  function codePoints(text) {
    return Array.from(text).length;
  }
  model.predict = function(transform, context) {
    var distribution = predict.call(this, transform, context);
    var right = (context && context.right) || '';
    if (!right) {
      return distribution;
    }
    var before = Array.from(context.left || '');
    var left = before.slice(0, Math.max(0, before.length - (transform.deleteLeft || 0))).join('')
      + (transform.insert || '');
    var breakWords = this.wordbreaker || this.breakWords;
    var after = breakWords(right);
    var leftWords = breakWords(left);
    if (!after.length || after[0].start !== 0 || !leftWords.length) {
      return distribution;
    }
    var last = leftWords[leftWords.length - 1];
    // The caret is inside a word when the word before it and the one after it are one word together.
    if (last.end !== left.length || breakWords(last.text + after[0].text).length !== 1) {
      return distribution;
    }
    var rest = after[0].text;
    // Keyman adds a space after a word chosen mid-word: the space already there goes, not doubled.
    var deleteRight = codePoints(rest) + (right.charAt(rest.length) === ' ' ? 1 : 0);
    for (var i = 0; i < distribution.length; i++) {
      var change = distribution[i].sample.transform;
      change.deleteRight = (change.deleteRight || 0) + deleteRight;
    }
    return distribution;
  };
  return model;
}
