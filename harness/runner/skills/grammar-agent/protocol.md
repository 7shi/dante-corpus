## 5-step reasoning protocol

Work through these steps in order for every parse unit. Think step by step in plain prose between tool calls; never state a fact about the text that a tool did not just show you.

### Step 1 - Discourse & quote boundaries

Call `read_unit` for the target unit. Read the quotes hierarchy first: direct speech spans and speaker boundaries decide whether a name is a vocative inside a quote or a subject of narration, and embedded quotes shift attribution. Note the unit bounds; every citation you make later must fall inside them.

### Step 2 - Predicates, agreement & voice

From Layer 2 morphology, enumerate every verbal token in the unit (finite verbs, participles, infinitives, gerunds). For each finite verb check person/number agreement against candidate nominative arguments: agreement with nothing visible means a pro-drop subject `(0, 0)`. Identify passive constructions and reflexive `si` before assigning roles.

### Step 3 - Case & core argument discrimination

Resolve pronouns and clitics through the pronoun case annex: case (nom / acc / dat / ...) decides `subj` vs `obj` vs `iobj`, not word order. Project Layer 4 UD relations onto roles (`nsubj` to `subj`, `obj` to `obj`, `iobj` to `iobj`, preposition-governed obliques to `obl:<prep>`). Use `search_corpus` when you need analogous constructions from other cantos to disambiguate. If Layer 2 or Layer 4 is defective beyond repair, say so explicitly and pass an `upstream_feedback` record with your validation call instead of forcing a reading.

### Step 4 - NP heads, clausal complements & control

Cite nominal arguments at their exact Layer 3 phrase-head tokens. Attach infinitival complements as `xcomp` when the complement subject is controlled by the matrix predicate, as `ccomp` otherwise; trace control chains across the whole unit so no predicate loses its arguments.
