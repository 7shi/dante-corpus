### The answer: the table you were given, filled in

You are given `<lines>` (the verse) and `<tokens>` (a table whose `Line` and `Token` columns are already filled in for you, one row per token, punctuation left out). Reason first, in prose — read what the lines are saying — then finish with exactly one `<words>` block holding **that same table, every row of it, in the same order, with the last two columns filled in**:

    <words>
    | Line | Token | Words | Part of Speech |
    |---|---|---|---|
    | copied | copied | the grammatical words, joined by + | one tag per word, joined by + |
    </words>

A token that is a single grammatical word repeats itself in the `Words` column — `| 4 | ciel | ciel | noun |` — because every token carries a judgment here, and a row that is missing is not a shorter answer, it is a refused one.

Example. Given:

    <lines>
    2 per l'universo penetra, e risplende
    3 in una parte più e meno altrove.
    </lines>

    <tokens>
    | Line | Token | Words | Part of Speech |
    |---|---|---|---|
    | 2 | per |  |  |
    | 2 | l' |  |  |
    | 2 | universo |  |  |
    | 2 | penetra |  |  |
    | 2 | e |  |  |
    | 2 | risplende |  |  |
    | 3 | in |  |  |
    | 3 | una |  |  |
    | 3 | parte |  |  |
    | 3 | più |  |  |
    | 3 | e |  |  |
    | 3 | meno |  |  |
    | 3 | altrove |  |  |
    </tokens>

the answer is:

    <words>
    | Line | Token | Words | Part of Speech |
    |---|---|---|---|
    | 2 | per | per | preposition |
    | 2 | l' | lo | article |
    | 2 | universo | universo | noun |
    | 2 | penetra | penetra | verb |
    | 2 | e | e | conjunction |
    | 2 | risplende | risplende | verb |
    | 3 | in | in | preposition |
    | 3 | una | una | article |
    | 3 | parte | parte | noun |
    | 3 | più | più | adverb |
    | 3 | e | e | conjunction |
    | 3 | meno | meno | adverb |
    | 3 | altrove | altrove | adverb |
    </words>

`l'` is one word with its vowel dropped before *universo*, so the answer writes it whole — `lo`, masculine here, which the line is what tells you. `e` occurs twice and takes two rows, one at each place — rows are matched to tokens by position, so a repeated token is never a problem.

A token written from several grammatical words is the one row that says more than the token already said, in both columns at once:

    | 4 | Nel | in+il | preposition+article |

### Rules, all of them mechanical

- Exactly one block, holding exactly one table.
- Every row of the given table, in the same order, none dropped and none added. Row *n* answers token *n*.
- `Line` and `Token` are copied from the table you were given — do not renumber, do not correct a spelling, do not strip an apostrophe, do not join two tokens into one row.
- `Words` is one word, or two or three joined by `+`. Never more than three, never an empty part, never a space inside a part.
- **A single word is the token with its dropped letters put back, and nothing else changed.** `ben` is `bene` and `ch'` is `che`; but `sanza` is `sanza`, `smarrita` is `smarrita`, `era` is `era`. The check applies this mechanically — your answer must contain the token's own letters unbroken and in order, growing only at an end the token's spelling opens — so a respelling or a dictionary form is refused.
- `Part of Speech` holds exactly as many tags as the second holds words, joined by `+`, each one of: `noun` `verb` `adjective` `adverb` `pronoun` `preposition` `article` `conjunction` `numeral` `interjection`. Nothing else is accepted — no blank, no "other", no subtype, no feature.
- Never answer with an index, a position, or a number. Positions are attached afterwards by the program from where each token actually sits; stating one here can only be wrong.
- No commentary inside the block, no extra columns, no notes column.

Your answer is checked mechanically the moment you send it. If the check refuses it you will be asked again, with the reason, and the refused answer is discarded — so send the whole table again, corrected.
