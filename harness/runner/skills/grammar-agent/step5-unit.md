### Step 5 - Intrinsic validation & self-correction

Submit all rows of the unit in one `validate_candidate` call. Read ok="false" payloads and error diagnostics literally: repair exactly what they name and call again. Iterate until the result reports `"valid": true`, then stop working and give your final answer: a short summary of the predicates, their roles, and any upstream feedback you filed. Never answer in prose alone without having validated a candidate.
