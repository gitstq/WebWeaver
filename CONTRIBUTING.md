# 🤝 Contributing to WebWeaver

Thank you for your interest in contributing to WebWeaver! This guide outlines the process for submitting contributions.

## 📋 How to Contribute

### Reporting Bugs 🐛
1. Check if the issue already exists in [Issues](https://github.com/gitstq/WebWeaver/issues)
2. If not, create a new issue with:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Python version and OS
   - Code snippets if applicable

### Submitting Pull Requests 🔧
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with clear comments
4. Add tests for new functionality
5. Ensure all tests pass (`python -m unittest discover -s tests`)
6. Commit with conventional commit format:
   - `feat: add new feature`
   - `fix: fix bug`
   - `docs: update documentation`
   - `refactor: code refactoring`
   - `test: add/update tests`
7. Push to your branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

### Code Standards 📝
- Follow PEP 8 style guidelines
- Add docstrings to all public classes and methods
- Include type hints for function signatures
- Write bilingual comments (Chinese + English) where helpful
- Keep zero external dependency principle

## 🌟 Contribution Ideas
- [ ] Add async/await support for concurrent crawling
- [ ] Implement JavaScript rendering detection
- [ ] Add proxy rotation support
- [ ] Build a web dashboard for monitoring crawls
- [ ] Add more extraction rule types
- [ ] Implement cookie/session management
- [ ] Add robots.txt parser and compliance checker

Thank you for your contributions! ❤️
