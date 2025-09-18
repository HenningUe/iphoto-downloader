# Python Vibe-Coding Agent Instruction Set

## Core Code Style Instructions

- Follow PEP 8 for indentation, line length, naming, and whitespace.
- **Maximum line length:** 99 characters per line (102 for docstrings).
- Pythonic linebreaks shall be applied. I.e. brackets are preffered, backslashed
  to be avoided.
- **Maximum module length:** Each module should not exceed 400 lines; split
  logic across modules if needed.
- **Naming conventions:**
  - Use `lowercase_with_underscores` for functions and variables.
  - Use `UPPER_CASE` for constants.
  - Class names use `CamelCase`.
  - Non-public members: prefix with a single underscore; use double underscore
    for name mangling in subclasses only.

## Type annotations

- add type annotations to all parameters and to all functions/methods as return
  types.
- use typing module as alias import, i.e. "import typing as tp". That means
  "Any" from typing is used as follows: "tp.Any"
- for type annotations use native types, e.g. dict. Do not use types defined in
  typing-module, e.g. Dict, Set, List from
- use pipe symbol "|" if multiple types are allowed. Do not use Union from
  typing-module
- use pipe symbol "|" and None for optional parameters. Do not use Optional from
  typing-module

## Exception handling

- Errors inside functions shall not be indicated by returning boolean values.
  I.e. returning "false" shall not be used to indicate function errors. Instead
  a proper custom error shall be thrown in the function. The caller can then
  deal with this function properly
- General try-except blocks handling flattly the whole function code block of
  every single function by a general Exception are not allowed. Instead
  try-except shall be applied very specifically on the code-lines where the
  error might occur. Only specific error types are allowed to catch (e.g.
  "ValueError"), not general errors, i.e. "Exception".
- The general try-except block handling is only allowed in very specific cases,
  e.g. on the main function in order to generally catch any unhandled exception
  and forward this to the developer.

## Testing related

- Create temporary files for quick test. Don't past the code to the console,
  otherwise ai agent (you) get stuck.
- Testing shall only be implemented using pytest.

  Keep classes focused. Super-classes with more than 300 lines or more than 30
  methods are forbidden Keep functions and methods focused. Functions and
  methods with more than 30 lines are forbidden.

## Function and Parameter Constraints

- **Maximum parameters per function:** 4 (consider grouping extra parameters in
  a data structure).
- **Function length:** Aim for under 30 lines per function; split complex logic
  into helpers.
- Avoid global mutable state except for constants.
- Include type hints for all function arguments and return types.

## Misc Python-related topics

- Any file/directory paths shall be only defined and handled via "pathlib.Path"
  class. File/directory paths shall not be treated with strings
- strings without context referencing via curled brackets should not have the
  f-prefix.

## Good-Code Rules

- Follow DRY: avoid duplication, always reuse logic.
- Use concise, meaningful docstrings for every public class, function, and
  module.
- Only add comments when necessary to clarify intent or edge cases.
- Validate inputs and handle errors explicitly; do not allow silent failures.
- Prefer immutable data structures when possible.
- Keep imports at the top of modules, and remove unused imports.
- Use well-defined exception classes for error handling.
- Document expected behaviors for all exposed APIs or functions.

## Agent-Specific Instructions

- Summarize actions performed—list created/modified files, key changes—after
  code generation.
- For ambiguous prompts, ask for clarification or use common/best-practice
  defaults.
- ensure previous functionality is preserved unless directed otherwise.
- Avoid deprecated APIs and patterns; check current documentation where
  possible.

## Folder and Project Structure

- Modules should be short and focused; split them by logical concern if they get
  long.
- Always include a README or instructions file, summarizing agent rules and
  constraints.
- Maintain consistent naming for files and folders.
- Remove unused files, boilerplate, and dead code unless required for
  compatibility.
