---
name: mintlify-fix
description: Use this skill to automatically find and fix Mintlify documentation errors. Trigger it when the user asks to "fix docs", "run validation", "fix mintlify errors", or uses the command "/mintlify-fix". This skill ensures MDX files comply with Mintlify's strict parsing rules.
---

# mintlify-fix

This skill automates the process of identifying and fixing formatting errors in Mintlify documentation.

## Underlying Logic & Best Practices

Always refer to the project's `CLAUDE.md` for specific formatting rules. The core goal is to achieve a "parsing loop" where `mintlify validate` returns no errors.

### Fix Protocols

1. **Tag Safety**: 
   - Pattern: `<` followed by a number or letter that isn't a valid MDX component.
   - Fix: Wrap in backticks. Example: `<2.0.0` becomes `` `<2.0.0` ``.

2. **Self-closing Tags**:
   - Pattern: `<br>` or `<br >`.
   - Fix: Convert to `<br/>`.

3. **Table Integrity**:
   - Every line in a table must start and end with `|`.
   - Column counts must be consistent across all rows (including the separator row).

4. **Frontmatter**:
   - Ensure `title` and `description` exist.
   - Colons must be followed by a space.
   - If `description` contains a colon, the entire value must be double-quoted.

5. **Mintlify Components**:
   - Use only official components: `Card`, `Callout`, `Tabs`, `Tip`, `Note`, `Warning`, `Accordion`, `Steps`, `Check`, `Frame`, `Snippet`.

## Workflow

1. **Detection**: Run `mintlify validate`.
   - If the output says "Validation successful!", report success to the user.
   - If errors are found, capture the file paths and error messages.

2. **Analysis**: Read the affected files. Pay close attention to the line numbers mentioned in the error log.

3. **Execution**:
   - Apply fixes systematically.
   - Do not guess fixes; if an error is ambiguous, use the surrounding context to determine the intent.
   - Prefer minimal changes that satisfy the validator.

4. **Verification**: Run `mintlify validate` again.
   - Repeat the loop if errors persist.
   - If the validator remains stuck on a file after 3 attempts, ask the user for clarification.

5. **Completion**: Once `mintlify validate` passes, summarize the fixes made and show evidence of the successful validation.
