# Contributing to CPM

Thank you for your interest in contributing to CPM! This document provides guidelines and instructions for contributing.

## Project Structure

```
cpm/
├── python/              # Python SDK and CLI
│   ├── cpm/             # Source code
│   ├── tests/           # Test suite
│   └── pyproject.toml   # Python package config
├── docs/                # Mintlify documentation
└── README.md            # Main documentation
```

## Getting Started

### Prerequisites

- Python 3.10+
- Git

### Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/transilienceai/cpm.git
   cd cpm/python
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

4. Run tests:
   ```bash
   pytest
   ```

## Development Workflow

### Making Changes

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following the coding standards

3. Add tests for new functionality

4. Run tests:
   ```bash
   pytest
   ```

5. Commit your changes:
   ```bash
   git commit -m "Add feature: description"
   ```

6. Push and create a pull request

### Coding Standards

#### Python Style

- Follow PEP 8
- Use type hints for function signatures
- Maximum line length: 100 characters
- Use descriptive variable names

```python
# Good
def resolve_component(
    comp_type: str,
    comp_name: str,
    shared_dir: Path,
) -> Optional[dict]:
    """Resolve a shared component by type and name."""
    ...

# Bad
def resolve(t, n, d):
    ...
```

#### Documentation

- All public functions must have docstrings
- Use Google-style docstrings
- Update docs/ when adding new features

#### Testing

- Write tests for all new functionality
- Use pytest fixtures for common setups
- Test both success and error cases

```python
class TestMyFeature:
    """Tests for my feature."""

    def test_success_case(self, setup_repo):
        """Test that feature works correctly."""
        result = my_feature(setup_repo)
        assert result is not None

    def test_error_case(self, setup_repo):
        """Test that feature handles errors."""
        with pytest.raises(ValueError):
            my_feature(invalid_input)
```

## Pull Request Guidelines

### Before Submitting

- [ ] Tests pass locally (`pytest`)
- [ ] Code follows style guidelines
- [ ] Documentation updated if needed
- [ ] Commit messages are clear and descriptive

### PR Title Format

Use conventional commit format:

- `feat: Add new feature`
- `fix: Fix bug in X`
- `docs: Update documentation`
- `refactor: Refactor X module`
- `test: Add tests for Y`

### PR Description

Include:

1. **Summary**: What does this PR do?
2. **Motivation**: Why is this change needed?
3. **Testing**: How was it tested?
4. **Breaking Changes**: Any breaking changes?

## Reporting Issues

### Bug Reports

Include:

- CPM version (`cpm --version`)
- Python version (`python --version`)
- Operating system
- Steps to reproduce
- Expected behavior
- Actual behavior
- Error messages/logs

### Feature Requests

Include:

- Use case description
- Proposed solution
- Alternatives considered

## Community

- Be respectful and inclusive
- Follow our [Code of Conduct](CODE_OF_CONDUCT.md)
- Help others in discussions

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

<p align="center">
  Thank you for contributing to CPM!
</p>

<p align="center">
  <a href="https://transilience.ai"><img src="docs/logo/transilience.png" alt="Transilience.ai" height="20" /></a>
</p>
