# Alt Project Guidelines

## Build & Environment Setup
- `./setup.sh` - Create Python 3.9.19 environment and install dependencies
- `./run.sh src/main.py` - Run the main process with proper PYTHONPATH

## Testing
- `./run.sh -m pytest src/tests/` - Run all tests
- `./run.sh -m pytest src/tests/test_constants.py` - Run a specific test file
- `./run.sh -m pytest src/tests/test_constants.py::test_creation` - Run a specific test function

## Linting & Type Checking
- `pre-commit run --all-files` - Run pre-commit hooks (black, check-yaml, etc.)
- `mypy src` - Run type checking with strict rules
- `black src` - Format code with black

## Code Style Guidelines
- Use type annotations for all function parameters and returns
- Follow strict mypy rules (disallow_untyped_calls, disallow_untyped_defs)
- Format code with black (line length 88 characters)
- Import order: standard library, third-party, local modules
- Use descriptive variable names in camelCase
- Classes use PascalCase, follow OOP principles with inheritance
- Provide docstrings for classes and functions
- Error handling: use exceptions with specific error types