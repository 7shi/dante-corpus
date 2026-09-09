### The answer: the table you were given, filled in

You are given `<lines>` (the verse) and `<table>` (a table whose `Line`, `Index` and `Token` columns are already filled in for you, one row per token, punctuation left out; `Index` numbers the rows from 1). Reason first, in prose — read what the lines are saying — then finish with exactly one `<table>` block of your own: **the same table, every row of it, in the same order, with the last two columns filled in**. The block goes out and comes back under the same name because it is the same table — you are filling it in, not writing a different one. Send it once, at the end; do not repeat the question's copy along the way.

    <table>
    | Line | Index | Token | Words | Part of Speech |
    |---|---|---|---|---|
    | copied | copied | copied | the grammatical words, joined by + | one tag per word, joined by + |
    </table>

A token that is a single grammatical word repeats itself in the `Words` column — `| 4 | 7 | ciel | ciel | noun |` — because every token carries a judgment here, and a row that is missing is not a shorter answer, it is a refused one.

Example. Given:

    <lines>
    2 per l'universo penetra, e risplende
    3 in una parte più e meno altrove.
    </lines>

    <table>
    | Line | Index | Token | Words | Part of Speech |
    |---|---|---|---|---|
    | 2 | 1 | per |  |  |
    | 2 | 2 | l' |  |  |
    | 2 | 3 | universo |  |  |
    | 2 | 4 | penetra |  |  |
    | 2 | 5 | e |  |  |
    | 2 | 6 | risplende |  |  |
    | 3 | 7 | in |  |  |
    | 3 | 8 | una |  |  |
    | 3 | 9 | parte |  |  |
    | 3 | 10 | più |  |  |
    | 3 | 11 | e |  |  |
    | 3 | 12 | meno |  |  |
    | 3 | 13 | altrove |  |  |
    </table>

the answer is:

    <table>
    | Line | Index | Token | Words | Part of Speech |
    |---|---|---|---|---|
    | 2 | 1 | per | per | preposition |
    | 2 | 2 | l' | lo | article |
    | 2 | 3 | universo | universo | noun |
    | 2 | 4 | penetra | penetra | verb |
    | 2 | 5 | e | e | conjunction |
    | 2 | 6 | risplende | risplende | verb |
    | 3 | 7 | in | in | preposition |
    | 3 | 8 | una | una | article |
    | 3 | 9 | parte | parte | noun |
    | 3 | 10 | più | più | adverb |
    | 3 | 11 | e | e | conjunction |
    | 3 | 12 | meno | meno | adverb |
    | 3 | 13 | altrove | altrove | adverb |
    </table>

`l'` is one word with its vowel dropped before *universo*, so the answer writes it whole — `lo`, masculine here, which the line is what tells you. `e` occurs twice and takes two rows, one at each place — rows are matched to tokens by position, so a repeated token is never a problem.

A token written from several grammatical words is the one row that says more than the token already said, in both columns at once:

    | 4 | 1 | Nel | in+il | preposition+article |

### Rules, all of them mechanical

- Exactly one block, holding exactly one table.
- Every row of the given table, in the same order, none dropped and none added. Row *n* answers token *n*.
- `Line`, `Index` and `Token` are copied from the table you were given — do not renumber, do not correct a spelling, do not strip an apostrophe, do not join two tokens into one row.
- **`Index` is the row's own number and it is given to you.** It is there so that a refusal can name a row and you can find it at once. Copy it; never work one out for yourself, and never let the numbers skip or repeat — if they do, a row has gone missing or been written twice.
- `Words` is one word, or two or three joined by `+`. Never more than three, never an empty part, never a space inside a part.
- **A single word is the token with its dropped letters put back, and nothing else changed.** `ben` is `bene` and `ch'` is `che`; but `sanza` is `sanza`, `smarrita` is `smarrita`, `era` is `era`. The check applies this mechanically — your answer must contain the token's own letters unbroken and in order, growing only at an end the token's spelling opens — so a respelling or a dictionary form is refused.
- `Part of Speech` holds exactly as many tags as the second holds words, joined by `+`, each one of: `noun` `verb` `adjective` `adverb` `pronoun` `preposition` `article` `conjunction` `numeral` `interjection`. Nothing else is accepted — no blank, no "other", no subtype, no feature.
- Beyond the three copied columns, never answer with a position or a number of your own. Where each token sits in the text is attached afterwards by the program; stating it here can only be wrong.
- No commentary inside the block, no extra columns, no notes column.

Your answer is checked mechanically the moment you send it. If the check refuses it you will be asked again, with the reason, and the refused answer is discarded — so send the whole table again, corrected.
