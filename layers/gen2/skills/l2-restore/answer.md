### The answer: one `<restore>` block listing only the tokens you changed

You are given `<lines>` (the verse) and `<tokens>` (the words it is made of, already
separated for you). Reason first, in prose, then finish with exactly one `<restore>` block
naming **only the tokens whose omitted letters you put back**:

    <restore>
    TOKEN:RESTORED
    </restore>

where `TOKEN` is copied from the token list and `RESTORED` is that same token with its
omitted letters put back. One row per token you changed, and no row for any other.

Every token you do **not** list is recorded exactly as written. That is the whole point of
the format: most tokens have left nothing out, and repeating them back says nothing.

When a passage has nothing to restore, send the block empty:

    <restore>
    </restore>

### Naming a token when the word alone is not enough

The key is normally just the token, copied from `<tokens>`. If that word appears **more
than once** in the passage, the key would not say which occurrence you mean, so put the
tokens that come before it in front of it, separated by spaces, until the key names exactly
one place — the token being restored is always the **last** word of the key:

    <restore>
    PRECEDING TOKEN:RESTORED
    </restore>

Use this only when you need it. If the same word occurs twice and is restored the same way
both times, you still need two rows, one for each occurrence, each with enough preceding
words to be unique. Two occurrences of one word can also be restored differently, which is
the other reason each occurrence gets its own row.

### Rules, all of them mechanical

- Exactly one block. One row per token you changed, and no row for any token you did not.
- Every key is copied verbatim from `<tokens>` — do not lowercase it, do not strip its
  apostrophe, do not correct its spelling, do not join two tokens into one word.
- A key must name exactly one place in the passage. If it names two, the answer is refused
  and you are told to add preceding words.
- The value is **one word**: no space, no `+`, no second word. A row whose value equals the
  key says nothing and is refused.
- The value must be **longer** than the key with its apostrophes removed, and must contain
  the key's own letters in their own order, unbroken — you never change the letters that
  are there.
- The value must grow **where the letters were left out**: at the end for a token with a
  trailing apostrophe, at the beginning for one with a leading apostrophe, and at the end
  only for a token with no apostrophe. A value that grows at the beginning of a token that
  does not begin with an apostrophe is refused.
- Never answer with an index, a position, or a number.
- Never answer with a lemma or a dictionary form.

Your answer is checked mechanically the moment you send it. If the check refuses it you
will be asked again, with the reason, and the refused answer is discarded — so send the
whole block again, corrected.
