# Contributing to FireFeed API

Thank you for considering contributing to FireFeed API! We welcome contributions from everyone.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to mail@firefeed.net.

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check the existing issues list. To create a bug report:

1. Use a clear and descriptive title
2. Describe the exact steps to reproduce the issue
3. Include your operating system and version
4. Include the version of FireFeed API you're using
5. Include any relevant error messages or logs

### Suggesting Enhancements

Enhancement suggestions are welcome! Please:

1. Use a clear and descriptive title
2. Describe the current behavior and the expected behavior
3. Explain why this enhancement would be useful
4. Include examples if possible

### Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Development Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Redis 6+

### Local Development

1. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/firefeed-api.git
   cd firefeed-api
   ```

2. Set up the development environment:
   ```bash
   ./firefeed-api/.kilocode_wrapper.sh setup-dev
   ```

3. Run the tests:
   ```bash
   ./firefeed-api/.kilocode_wrapper.sh run-tests
   ```

4. Start the development server:
   ```bash
   ./firefeed-api/.kilocode_wrapper.sh start-dev
   ```

### Code Style

We use `ruff` for linting and formatting. Before submitting your changes:

```bash
# Run linting
./firefeed-api/.kilocode_wrapper.sh run-lint

# Run type checking
./firefeed-api/.kilocode_wrapper.sh run-type-check
```

### Testing

We use `pytest` for testing. Please ensure all tests pass:

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=firefeed-api --cov-report=html

# Run specific test file
pytest tests/test_backward_compatibility.py
```

### Documentation

Please update documentation when adding new features:

- Update this file if needed

## Development Guidelines

### Architecture

- Follow the microservices architecture pattern
- Maintain backward compatibility
- Use dependency injection for loose coupling
- Implement proper error handling
- Use async/await for I/O operations

### Code Quality

- Write clear, readable code
- Add appropriate comments and docstrings
- Follow Python naming conventions
- Use type hints
- Write tests for new functionality

### Security

- Never commit secrets or API keys
- Use environment variables for configuration
- Validate all user input
- Follow security best practices
- Report security vulnerabilities privately

### Performance

- Use caching appropriately
- Optimize database queries
- Use pagination for large datasets
- Monitor memory usage
- Consider async operations for I/O

## Issue Labels

We use the following labels to categorize issues:

- `bug` - Something isn't working
- `enhancement` - New feature or request
- `documentation` - Improvements or additions to documentation
- `help wanted` - Extra attention is needed
- `good first issue` - Good for newcomers
- `question` - Further information is requested
- `wontfix` - Will not be worked on
- `duplicate` - This issue or pull request already exists

## Release Process

1. Create a release branch
2. Update version numbers
3. Update changelog
4. Run comprehensive tests
5. Create release tag
6. Deploy to staging
7. Deploy to production

## Getting Help

- Check the [documentation](https://docs.firefeed.net)
- Search existing [issues](https://github.com/firefeed-net/firefeed-api/issues)
- Ask questions in [discussions](https://github.com/firefeed-net/firefeed-api/discussions)
- Contact the team at mail@firefeed.net

## Contributing Agreement

By contributing to this project, you agree to license your contributions under the MIT License.

## Questions?

If you have any questions about contributing or need help getting started, please reach out to us at mail@firefeed.net or open an issue with the `question` label.

Thank you for contributing to FireFeed API! 🚀