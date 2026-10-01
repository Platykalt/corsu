/*
  Corsu: Corsican word prediction and correction for Keyman.
  wordlist.tsv is generated from the Corsu lexicon by tools/build_keyboard.py.
*/

const source: LexicalModelSource = {
  format: 'trie-1.0',
  wordBreaker: 'default',
  sources: ['wordlist.tsv'],
};
export default source;
