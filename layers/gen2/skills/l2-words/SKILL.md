---
name: l2-words
description: Reads a few lines of Dante's Divina Commedia and answers, for every token, the grammatical words it is written from and one coarse part of speech for each of them.
resources:
  answer.md: The answer contract - one <words> block holding the table the question supplies, filled in, one row per token.
---

You answer two things about every token of a few lines at a time, and you answer them together:

1. **which grammatical words it is written from** — one, usually; two or three when several words are fused into one written token;
2. **what each of those words is** — one part of speech, from a closed list of ten.

This is the *Divina Commedia*, so the language is fourteenth-century Florentine. You are given a short passage and a table of the tokens it is made of, already separated for you and already labelled with the line each one sits on — you fill in the two columns that are blank. There is nothing you answered before: every request is a fresh, complete question about the tokens in front of you.

**Read the passage as verse before you fill in anything.** The table is a convenience for recording the answer, not the thing being analysed: what is being analysed is three lines of poetry, and a token's answer is only right if it is right in the sentence those lines make.

**The two questions are one question.** A token is not decided by its shape — it is decided by what it does in the line. The same letters can be a fused preposition and article in one place and a plain noun in another, and the way to tell is to read the line: if calling a token two words forces you to write a part of speech that cannot stand where it stands — a preposition where the line needs a noun, an article with no noun to go with it, an adjective agreeing with nothing — then it is not two words. Answer the analysis the whole line can carry.

## The tokens, and the order

You send back **every row of the table you were given, in the same order**, including the ones that are ordinary single words. Nothing is skipped and nothing is added, and the `Line` and `Token` columns come back exactly as they were given; the check refuses an answer where they do not.

Punctuation is not in the table and is never answered.

## The first column: the grammatical words

Split a token when the letters on the page spell out **more than one grammatical word fused into one written token**. The Italian cases are:

- **Preposition + article contractions**: `nel` = `in` + `il`, `del` = `di` + `il`, `al` = `a` + `il`, `dal` = `da` + `il`, `col` = `con` + `il`, `sul` = `su` + `il`, and their inflected forms (`nella`, `degli`, `ai`, `dalle`, …).
- **Verb + enclitic pronoun**: `vagliami` = `vaglia` + `mi`, `venendomi` = `venendo` + `mi`, `farlo` = `fare` + `lo`. Two enclitics are possible: `dirtelo` = `dire` + `te` + `lo`.
- **Other clitic compounds**: pronoun + pronoun (`glielo` = `gli` + `lo`), pronoun + preposition, adverb + pronoun (`vene` = `ve` + `ne`).

Each part is written as the whole ordinary form of that grammatical word — a contraction gives `in` and `il`, never `n` and `el`; a verb that dropped its ending before the pronoun gives it back, so `farne` is `fare` + `ne` and not `far` + `ne`. Every part is a real word of the language, and the parts stand in the order the token writes them.

**A word that has dropped letters is written whole.** This is the one thing you may change about a token: put back the letters the page leaves out, where the page says they were left out. You may not put back anything else — no dictionary form, no different word.

- **Elision** — a word whose vowel is dropped next to another word, marked with an apostrophe: `ch'`, `l'`, `d'`, `i'`, `v'`, `Tant'`, `com'`, `'l`, `'n`. **One grammatical word**, and the answer is the whole word: `ch'` is `che`, `i'` is `io`, `'l` is `il`, `Tant'` is `Tanto`. The apostrophe says at which end the letters go, so they go there and nowhere else. `l'` is `lo` or `la` — read the line and say which; before a feminine plural it can be `le`.
- **Apocope** — a word whose final syllable is dropped with no apostrophe: `cammin` is `cammino`, `ben` is `bene`, `dir` is `dire`, `pensier` is `pensiero`, `qual` is `quale`, `son` is `sono`.
- **Ordinary words of any length or part of speech** — nouns, verbs, adjectives, adverbs, articles, plain prepositions, conjunctions, pronouns, interjections, proper names. One grammatical word, and it has dropped nothing, so it is copied back as written.

**What is not a dropped letter, and must be copied back untouched.** Modern Italian descends from this language: most of what looks old is not a shortened word at all, it is simply this language's word, and changing it invents a text Dante did not write.

- **A different spelling is not a truncation.** `sanza` is `sanza`, not *senza*. `core` is `core`. `giuso` is `giuso`. `aveva` and `avea` are two forms, and `avea` is not `aveva` shortened.
- **A dictionary form is not a restoration.** `smarrita` is `smarrita`, never *smarrito*; `nostra` is `nostra`; `era` is `era`, never *essere*. Gender, number, person, tense and mood are all left exactly as the page writes them — a later pass reads them off this word.
- The test to apply, in both directions: **the token's own letters must still read straight through your answer, unbroken and in order, with the new letters only at the end the token's own spelling opens.** `pensier` -> `pensiero` passes. `sanza` -> `senza` does not. A word that fails this test is copied back as written.
- **A token that merely *contains* the letters of a shorter word.** `della` is two words (*di* + *la*); `bella` is one adjective that happens to begin with the same letters. Ask what the token *means and does* in the grammar, never what substrings you can find in it.
- **A word that is historically compound but is now a single word**: `perché`, `poiché`, `senza`, `ancora`, `sempre`, `dunque`. One grammatical word.

When splitting and not splitting are both arguable, **read the line and let the parts of speech decide**; where they still both work, do not split. A token wrongly left whole is one missing distinction; a token wrongly torn apart invents grammatical words that are not there and puts false parts of speech in the line.

## The second column: the part of speech

Exactly one tag per grammatical word, from this closed list of ten, and nothing else:

`noun` `verb` `adjective` `adverb` `pronoun` `preposition` `article` `conjunction` `numeral` `interjection`

The list is coarse on purpose. Finer distinctions — gender, number, person, tense, mood, and the subtypes of each category — are a later pass's, over the words this one settles. So:

- **A proper name is `noun`.** There is no separate tag for it.
- **A relative, interrogative, demonstrative, personal or indefinite pronoun is `pronoun`** — including the relative `che`, and including a clitic like `mi`, `ti`, `si`, `ne`, `lo`.
- **A possessive or demonstrative modifier is `adjective`** (`mio`, `nostra`, `quel` before a noun); standing on its own for a noun, it is `pronoun`.
- **A participle is `verb`**, always — past or present, and whether it stands in a compound tense, predicatively, or in front of a noun like an adjective. This one is a convention of this pass, not a judgment left to the passage: do not retag a participle `adjective` because it reads like one here.
- **An infinitive, a gerund, an imperative are `verb`.**
- **A number word is `numeral`** whether it counts (`due`, `mille`) or orders (`primo`).
- **An article is `article`** — definite or indefinite, and the elided `l'`, `'l`, `un'`.
- **An exclamation or address particle is `interjection`** (`Ahi`, `Oh`, `deh`).

Where a category is genuinely arguable in the line — an adjective used adverbially, a participle in an absolute construction — pick the one the line's syntax supports and move on. There is no "other" tag and no blank: every word gets one of the ten.
