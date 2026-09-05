## 4-step reasoning protocol

Work through these steps in order for the parse unit in front of you. Think step by step in plain prose before you answer; never state a fact about the text that the evidence in this message does not show you.

### Step 1 - Discourse & quote boundaries

Read the quotes hierarchy first: direct speech spans and speaker boundaries decide whether a name is a vocative inside a quote or a subject of narration, and embedded quotes shift attribution. Note the unit bounds; every citation you make must fall inside them.

### Step 2 - Predicates, agreement & voice

From Layer 2 morphology, enumerate every verbal token in the unit (finite verbs, participles, infinitives, gerunds). For each finite verb check person/number agreement against candidate nominative arguments: agreement with nothing visible means a pro-drop subject `(0, 0)`. Identify passive constructions and reflexive `si` before assigning roles.

### Step 3 - Case & core argument discrimination

Resolve pronouns and clitics through the pronoun case annex: case (nom / acc / dat / ...) decides `subj` vs `obj` vs `iobj`, not word order. Project Layer 4 UD relations onto roles (`nsubj` to `subj`, `obj` to `obj`, `iobj` to `iobj`, preposition-governed obliques to `obl:<prep>`). If Layer 2 or Layer 4 is defective beyond repair, say so explicitly in your prose and give the reading the rest of the evidence supports rather than forcing one the defective layer would dictate.

### Step 4 - NP heads, clausal complements & control

Cite nominal arguments at their exact Layer 3 phrase-head tokens. Attach infinitival complements as `xcomp` when the complement subject is controlled by the matrix predicate, as `ccomp` otherwise; trace control chains across the whole unit so no predicate loses its arguments.
