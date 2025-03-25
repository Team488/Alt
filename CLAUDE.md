# Alt Codebase Guide for Agentic Coding

## Commands
- Run tests: `python -m pytest src/tests`
- Run single test: `python -m pytest src/tests/test_file.py::test_function`
- Typecheck: `mypy src`
- Typecheck file: `mypy src/path/to/file.py`
- Run script: `./Scripts/run.sh src/script_name.py`

## Code Style
- Python 3.9+ with gradual typing implementation
- Import order: standard library, third-party, local modules
- Type annotations required for new code (use typing module)
- Use Optional[Type] for nullable values, Union[Type1, Type2] for multiple types
- Class methods should have type annotations for parameters and return values
- Variable naming: snake_case for variables/functions, PascalCase for classes
- Error handling: use try/except blocks with specific exceptions
- Abstract base classes in src/abstract/ define core interfaces
- Agents inherit from appropriate base classes in src/Core/Agents/Abstract/
- Follow existing patterns in fully-typed files (see gradual_typing.md)

## Testing
- Write unit tests in src/tests/ directory
- Test files should be named test_*.py
- Test functions should be named test_*