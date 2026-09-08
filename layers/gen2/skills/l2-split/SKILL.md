---
name: l2-split
description: Splits the tokens of a few lines of Dante's Divina Commedia into the grammatical words each is composed of, leaving tokens that are already one word alone.
resources:
  answer.md: The answer contract - one <split> block naming only the tokens that split, keyed by the word, never by an index.
---

You decide, for each token of a few lines at a time, whether it is **one grammatical word or several written together**, and you report **only the ones that are several**.

This is the *Divina Commedia*, so the language is fourteenth-century Florentine. You are given a short passage and the list of tokens it is made of, already separated for you. There is nothing you answered before: every request is a fresh, complete question about the tokens in front of you.

**Read every token; list only the composite ones.** A token you do not mention is recorded as a single word, which is the right answer for most of them. Most passages yield one or two rows, and many yield none.

**The lines are there for context, not for analysis.** You are not parsing the sentence, not assigning parts of speech, and not translating — the only question is whether each written token is one grammatical word or several fused together.

## What counts as a split

Split a wordform when the letters on the page spell out **more than one grammatical word fused into one written token**. The Italian cases are:

- **Preposition + article contractions**: `nel` = `in` + `il`, `del` = `di` + `il`, `al` = `a` + `il`, `dal` = `da` + `il`, `col` = `con` + `il`, `sul` = `su` + `il`, and their inflected forms (`nella`, `degli`, `ai`, `dalle`, …).
- **Verb + enclitic pronoun**: `vagliami` = `vaglia` + `mi`, `venendomi` = `venendo` + `mi`, `dimmi` = `di` + `mi`, `farlo` = `far` + `lo`. Two enclitics are possible: `dirtelo` = `dir` + `te` + `lo`.
- **Other clitic compounds**: pronoun + pronoun (`glielo` = `gli` + `lo`), pronoun + preposition, adverb + pronoun (`vene` = `ve` + `ne`).

Answer each part as the ordinary form of that grammatical word — `nel` splits to `in` and `il`, not to `n` and `el`. Every part must be a real word of the language, and the parts in the order the wordform writes them.

## What is NOT a split, and is therefore not listed at all

**These are the cases you are most likely to get wrong, so read them before answering.**

- **Elision** — a word whose final vowel is dropped before another word, marked with an apostrophe: `ch'`, `l'`, `d'`, `i'`, `v'`, `Tant'`, `com'`, `'l`, `'n`. These are **one grammatical word**, written short. `ch'` is the single word *che*. `i'` is the single word *io*. Do not list them, and do **not** restore the missing letter — restoring spelling is a different job, done later, by someone else.
- **Apocope** — a word whose final syllable is dropped with no apostrophe: `cammin` (for *cammino*), `ben` (for *bene*), `dir` (for *dire*), `pensier` (for *pensiero*), `qual` (for *quale*), `son` (for *sono*), `gran`, `vuol`, `avea`. One grammatical word each. Do not list them, do not restore them.
- **Ordinary words of any length or part of speech** — nouns, verbs, adjectives, adverbs, articles, plain prepositions, conjunctions, pronouns, interjections, proper names. `mezzo`, `ritrovai`, `selvaggia`, `oscura`, `dirò`, `paura`, `per`, `che`, `e`, `Ahi`. One grammatical word; not listed.
- **A word that merely *contains* the letters of a shorter word.** `della` splits (it is *di* + *la*); `bella` does not (it is one adjective that happens to begin with the same letters). Ask what the word *means and does* in the grammar, never what substrings you can find in it.
- **A word that is historically compound but is now a single word**: `perché`, `poiché`, `senza`, `ancora`, `sempre`, `dunque`. One grammatical word.

When in doubt between splitting and not splitting, **do not split** — leave it off the list. A wordform wrongly left whole is one missing distinction; a wordform wrongly torn apart invents grammatical words that are not there.

## Ambiguity

A very few wordforms genuinely split more than one way. `nel` is the real example: ordinarily the contraction `in` + `il`, but in some passages the pronoun compound `ne` + `lo`. Here you *do* have the line in front of you, so use it: answer the reading that is right in this passage.
