# Contributing to Genesis Studio

Thank you for your interest in contributing to the Vertex Genesis project!

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/genesis-studio.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Make your changes
5. Test thoroughly
6. Commit with clear messages: `git commit -m "Add feature: description"`
7. Push to your fork: `git push origin feature/your-feature-name`
8. Open a Pull Request

## Development Setup

```bash
# 1. Clone and set up the orchestrator first
git clone https://github.com/brian95240/universal-living-memory.git core
cd core
python genesis.py
docker compose up -d

# 2. Return to studio directory
cd ..

# 3. Install studio dependencies
pip install -r studio/requirements.txt

# 4. Launch studio
python studio/genesis_studio.py
```

## Code Standards

- Follow PEP 8 for Python code
- Add docstrings to functions and classes
- Keep UI components modular and reusable
- Test voice interaction flows
- Ensure `.gitignore` is comprehensive

## Testing Guidelines

- Test with the orchestrator running
- Verify voice input/output functionality
- Test interrupt mechanisms
- Validate multi-agent workflows
- Check error handling for orchestrator failures

## Pull Request Guidelines

- Provide a clear description of changes
- Reference related issues
- Include screenshots for UI changes
- Update documentation as needed
- Ensure compatibility with orchestrator API

## Code Review Process

1. Maintainers will review PRs within 7 days
2. Address feedback and requested changes
3. Once approved, maintainers will merge

## Questions?

Open an issue for questions or discussions.

## License

By contributing, you agree that your contributions will be licensed under the AGPL-3.0 license.
