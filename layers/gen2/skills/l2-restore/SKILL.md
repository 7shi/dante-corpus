---
name: l2-restore
description: Restores the letters an L1 token leaves out — the letters an apostrophe stands for, or an omitted final syllable — leaving every other token exactly as written.
resources:
  answer.md: The answer contract - one <restore> block naming only the tokens whose letters were restored, keyed by the word, never by an index.
---

You are given a few lines of the *Divina Commedia* and the tokens they are made of. For
each token you decide **whether letters have been left out of it**, and if so you write the
token with those letters put back.

You report **only the tokens you changed**. A token you do not mention is recorded exactly
as written, which is the right answer for most of them.

This is fourteenth-century Florentine, and the poem is metrical: a word is shortened when
the line needs it to be. Putting the letters back is the whole job.

## The only two things you restore

1. **An apostrophe stands for letters that were left out.** Put those letters back, at the
   apostrophe's own position — a trailing apostrophe means letters were left out at the end
   of the word, a leading one means they were left out at the beginning.

2. **A final syllable left out with no apostrophe to mark it.** The word simply ends early.
   Put the rest of it back.

That is all. Nothing else is restored.

## The rule that decides every case

**You never change a letter that is there.** The token's own letters must still read
straight through your answer, in the same order, unbroken. You only ever put letters back
where the word left them out:

- a **trailing** apostrophe: your answer grows at the end;
- a **leading** apostrophe: your answer grows at the beginning;
- **no** apostrophe: your answer can only grow at the end, because an omitted final
  syllable is the only thing left to restore.

So a word gains letters at its beginning **only** when it begins with an apostrophe. Your
answer is checked against all of this mechanically, and a row that breaks it is refused.

## What you must NOT do

- **Do not modernize a word.** A word spelled differently from the way today's Italian
  spells it is not a shortened word — it is this language's own word, spelled its way, and
  today's spelling descends from it. Nothing has been left out of it, so it is not listed.
  Restoring omitted letters is the job; respelling a word is not, and nobody has asked for
  it.
- **Do not give a dictionary form.** A finite verb written in full stays as it is: you
  restore letters the word left out, you do not conjugate backwards, and you do not replace
  an inflected form with its infinitive or its singular.
- **Do not split a word into two.** Whether a token is several grammatical words fused
  together is a different question, asked later, by someone else. Your answer is always
  **one word**, never two words with a space.
- **Do not touch a word that is already whole.** Most tokens have left nothing out. They
  are not listed.
- **Do not touch punctuation.**

## Read the line, not just the word

A word that has left letters out can look exactly like a different word that has not, and a
word that has left nothing out can look exactly like a shortened one. Spelling alone cannot
tell you which of the two you are holding; only what the word is doing in the line can.

So for every token, ask **what it means where it stands**, and answer from that — never
from what other word it resembles.

## When you are unsure

**Leave the token alone.** A word left as written is one restoration missing; a word given
letters it never left out is an invention, and it travels into everything built on top of
this.
