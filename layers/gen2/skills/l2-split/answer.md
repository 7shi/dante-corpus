### The answer: one `<split>` block listing only the tokens that split

You are given `<lines>` (the verse) and `<tokens>` (the words it is made of, already separated for you). Reason first, in prose, then finish with exactly one `<split>` block naming **only the tokens that are several grammatical words written together**:

    <split>
    word:part+part
    </split>

Every token you do **not** list is recorded as a single word. That is the whole point of the format: most tokens are single words, and repeating them back says nothing.

Example. Given:

    <lines>
    1 Nel mezzo del cammin di nostra vita
    2 mi ritrovai per una selva oscura,
    3 ché la diritta via era smarrita.
    </lines>

    <tokens>
    Nel mezzo del cammin di nostra vita mi ritrovai per una selva oscura ché la diritta via era smarrita
    </tokens>

the whole answer is two rows:

    <split>
    Nel:in+il
    del:di+il
    </split>

`cammin` is not listed: it is *cammino* with its last syllable dropped, which is one word written short, and restoring spelling is a different job done later by someone else. `ché`, `la`, `mi` and the rest are single words too, so they are not listed either.

When a passage holds no composite token at all, send the block empty:

    <split>
    </split>

### Naming a token when the word alone is not enough

The key is normally just the token, copied from `<tokens>`. If that word appears **more than once** in the passage, the key would not say which occurrence you mean, so put the tokens that come before it in front of it, separated by spaces, until the key names exactly one place — the token being split is always the **last** word of the key:

    <split>
    trattar del:di+il
    </split>

Use this only when you need it. If the same word occurs twice and splits the same way both times, you still need two rows, one for each occurrence, each with enough preceding words to be unique.

### Rules, all of them mechanical

- Exactly one block. One row per token that splits, and no row for any token that does not.
- Every key is copied verbatim from `<tokens>` — do not lowercase it, do not strip its apostrophe, do not correct its spelling, do not join two tokens into one word.
- A key must name exactly one place in the passage. If it names two, the answer is refused and you are told to add preceding words.
- Every row splits: between two and three parts, each a non-empty run of letters with no spaces. A row whose value is one word says nothing and is refused.
- Never answer with an index, a position, or a number. Positions are attached afterwards by the program from where each token actually sits; stating one here can only be wrong.
- Never answer with a lemma or a dictionary form. `ben` is not listed at all; it is certainly not `ben:bene`.

Your answer is checked mechanically the moment you send it. If the check refuses it you will be asked again, with the reason, and the refused answer is discarded — so send the whole block again, corrected.
