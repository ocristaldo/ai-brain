# Contributing to AI Brain Vault

Thank you for your interest in contributing to AI Brain Vault! This document provides guidelines for contributing to the project.

---

## How to Contribute

### Reporting Bugs

1. **Check existing issues** - Search [GitHub Issues](https://github.com/ocristaldo/ai-brain/issues) to see if it's already reported
2. **Create detailed report** - Include:
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - System info (OS, Python version)
   - Relevant logs from `logs/`

### Suggesting Features

1. **Check roadmap** - Review the GitHub milestones and project board for planned features
2. **Open discussion** - Create an issue labeled `enhancement`
3. **Provide context** - Explain the use case and benefits

### Contributing Code

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Test thoroughly**
   ```bash
   source .venv/bin/activate
   pytest tests/ -v
   ```
5. **Commit with clear messages**
   ```bash
   git commit -m "Add: Feature description"
   ```
6. **Push and create Pull Request**

---

## Development Setup

```bash
# Clone your fork
git clone https://github.com/ocristaldo/ai-brain.git
cd ai-brain

# Deploy
./deploy.sh

# Run tests
source .venv/bin/activate
pytest tests/ -v

# Check code style
flake8 scripts/ tests/
```

---

## Code Style

- **Python**: Follow PEP 8
- **Line length**: 120 characters max
- **Docstrings**: Use for all functions
- **Type hints**: Encouraged but not required

### Example

```python
def validate_facets(meta: dict) -> None:
    """
    Validate facet values in note metadata.

    Args:
        meta: Dictionary containing note metadata

    Raises:
        ValueError: If any facet has invalid value
    """
    enums = {
        "domain": {"work", "personal", "hobbies"},
        ...
    }
    for k, allowed in enums.items():
        if k not in meta or meta[k] not in allowed:
            raise ValueError(f"Invalid {k}")
```

---

## Testing Guidelines

### Required Tests

All new features must include tests:

- **Unit tests**: Test individual functions
- **Integration tests**: Test full workflows
- **Edge cases**: Test error handling

### Running Tests

```bash
# All tests
pytest tests/ -v

# Specific test file
pytest tests/test_search.py -v

# With coverage
pytest tests/ --cov=scripts --cov-report=html
```

---

## Documentation

### Updating Documentation

When adding features, update:

1. **README.md** - User-facing documentation
2. **docs/** - Detailed guides
3. **Docstrings** - Code documentation
4. **CHANGELOG.md** - Version changes (create if doesn't exist)

### Documentation Standards

- **Clear and concise**
- **Include examples**
- **Update FAQ** in README.md for common questions
- **Code examples** should be runnable

---

## Commit Messages

Follow conventional commits:

```
type: subject

body (optional)

footer (optional)
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `test`: Adding tests
- `refactor`: Code restructuring
- `perf`: Performance improvement
- `chore`: Maintenance tasks

### Examples

```
feat: Add semantic search with vector embeddings

Implements semantic search using sentence transformers.
Integrates with existing FTS search as hybrid approach.

Closes #42
```

```
fix: Handle malformed YAML frontmatter gracefully

Previously crashed on invalid YAML. Now logs warning
and skips the file.

Fixes #38
```

---

## Pull Request Process

1. **Update documentation** - README, docs/, code comments
2. **Add tests** - Ensure coverage for new code
3. **Run full test suite** - All tests must pass
4. **Update CHANGELOG** - Document your changes
5. **Request review** - Tag maintainers
6. **Address feedback** - Make requested changes
7. **Squash commits** - Keep history clean

### PR Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Documentation updated
- [ ] Tests added/updated
- [ ] CHANGELOG updated
- [ ] No breaking changes (or documented)
```

---

## Project Structure

```
ai-brain/
├── scripts/          # Core functionality
├── tests/            # Test suite
├── docs/             # Documentation
├── notes/            # Example notes (not in git)
├── config.yaml       # Configuration
├── Makefile          # Command shortcuts
├── deploy.sh         # Deployment script
├── delete.sh         # Cleanup script
└── requirements.txt  # Python dependencies
```

### Adding New Scripts

1. Place in `scripts/` directory
2. Use `common.py` for shared utilities
3. Add to `Makefile` if user-facing
4. Document in README.md

---

## Areas for Contribution

### High Priority

- [ ] Real vector embeddings (Ollama integration)
- [ ] Additional test coverage
- [ ] Performance benchmarks
- [ ] Multi-device sync (planned for v2.0)

### Medium Priority

- [ ] Rich console output
- [ ] Stats dashboard
- [ ] Graph visualization
- [ ] Web UI (planned for v3.0)

### Good First Issues

- [ ] Improve error messages
- [ ] Add more example notes
- [ ] Documentation improvements
- [ ] Code comments

---

## Questions?

- **GitHub Issues**: For bugs and features
- **Discussions**: For general questions
- **Email**: [Maintainer email if public]

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive experience for everyone.

### Our Standards

- **Be respectful** of differing viewpoints
- **Be constructive** in feedback
- **Be collaborative** in approach
- **Be patient** with newcomers

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Publishing private information
- Unprofessional conduct

### Enforcement

Violations may result in temporary or permanent ban from the project.

---

Thank you for contributing to AI Brain Vault! 🧠
