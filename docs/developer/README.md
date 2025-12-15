# Developer Documentation

Architecture, testing guides, and contribution documentation for Obsidian CLI Ops.

## 📂 Contents

### Core Documentation

- **[Architecture](architecture.md)** - Three-layer system design (890 lines)
  - Presentation → Application → Data layers
  - Module structure and dependencies
  - Design patterns and best practices

### [Testing](testing/)

- **[Overview](testing/overview.md)** - Complete test suite summary
  - 298 tests, 70% coverage
  - Test organization and commands
- **[Core Tests](testing/core-tests.md)** - Core layer test details
  - VaultManager, GraphAnalyzer, Models
  - 97 tests for business logic
- **[Sandbox Testing](testing/sandbox.md)** - Comprehensive testing guide
  - Synthetic vault generator
  - Testing workflows
- **[Sandbox Quick Ref](testing/sandbox-quick-ref.md)** - Quick reference card

### [Research](research/)

- **[CLI/GUI Best Practices](research/cli-gui-practices.md)** - Research notes
  - Architecture patterns
  - Industry best practices
  - Implementation status

---

## 🎯 For New Contributors

**Getting Started:**

1. Read [Architecture](architecture.md) to understand the system
2. Review [Testing Overview](testing/overview.md) for test commands
3. Check [CLAUDE.md](../../CLAUDE.md) for development workflow
4. See [.claude/rules/](../../.claude/rules/) for detailed rules

**Key Concepts:**

- **Three-Layer Architecture:** Presentation → Application → Data
- **Zero Duplication:** CLI and TUI share 100% of business logic
- **Domain Models:** Vault, Note, ScanResult, GraphMetrics, VaultStats
- **Testing:** 298 tests across all layers

---

## 🔧 Quick Commands

```bash
# Run tests
npm test                    # Jest tests
pytest src/python/tests/    # Python tests

# Test specific layer
pytest src/python/tests/core/              # Core layer
pytest src/python/tests/test_db_manager.py # Database

# View architecture
cat docs/developer/architecture.md
```

---

## 📊 Project Stats

- **Total Lines:** ~11,500
- **Python:** ~7,500 lines (15 modules)
- **ZSH:** ~680 lines
- **Tests:** 298 tests (124 Python + 40 Jest + 4 Shell)
- **Coverage:** ~70% overall

---

[← Back to Documentation Index](../README.md)
