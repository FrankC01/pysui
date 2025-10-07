# PySui Security Guidelines

## 🔒 Security Scanning Tools

PySui project uses dual security scanning tools:
- **Bandit** - Python code security analysis
- **pip-audit** - Dependency vulnerability scanning

## Quick Start

```bash
# Install development dependencies (includes both security tools)
pip install -r requirements-dev.txt

# Run code security scanning (Bandit)
bandit -r pysui/ --severity-level medium

# Run dependency security scanning (pip-audit)
pip-audit
```

## Recommended Scanning Commands

### 🐍 Bandit (Code Security)

```bash
# Daily development check (medium-high priority)
bandit -r pysui/ --severity-level medium --confidence-level medium

# Complete security check
bandit -r pysui/ --severity-level low --confidence-level low

# Generate reports
bandit -r pysui/ --severity-level medium --format json --output bandit-report.json
```

### 🔗 pip-audit (Dependency Security)

PySui uses **setuptools + pyproject.toml** for dependency management, with a traditional `requirements.txt` file. Here are the recommended scanning approaches:

```bash
# Scan pyproject.toml dependencies (recommended for PySui)
pip-audit --requirement <(python -c "import sys; sys.path.append('pysui'); from sui_constants import DEFAULT_SUI_CLIENT_CONFIG; print('pyproject.toml')")

# Scan traditional requirements.txt
pip-audit -r requirements.txt

# Scan installed packages in current environment
pip-audit

# Scan development dependencies
pip-audit -r requirements-dev.txt

# Generate detailed report
pip-audit --format=json --output audit-report.json

# Check for fixes available
pip-audit --fix

# Dry run fix check
pip-audit --fix --dry-run

# Scan project directory (detects dependency files automatically)
pip-audit --path .
```

### 🔄 Combined Scanning

```bash
# Complete security scan (code + dependencies)
bandit -r pysui/ --severity-level medium
pip-audit -r requirements.txt -r requirements-dev.txt
```

## Common Security Issues

### 🐍 Bandit Detected Issues

1. **Private Key Management** - Hardcoded private keys, insecure key storage
2. **Dynamic Code Execution** - Use of exec() and eval()
3. **Network Communication** - SSL/TLS configuration issues
4. **Cryptographic Operations** - Insecure hash algorithms, random number generation

### 🔗 pip-audit Detected Issues

1. **Dependency Vulnerabilities** - Security vulnerabilities in third-party libraries
2. **Outdated Versions** - Known vulnerabilities in old versions
3. **Supply Chain Security** - Security issues in dependencies of dependencies
4. **Package Integrity** - Verification of package hashes and sources

## Special Focus for PySui

### Package Management Setup
PySui uses a hybrid dependency management approach:
- **Primary**: `pyproject.toml` with setuptools backend
- **Traditional**: `requirements.txt` for runtime dependencies
- **Development**: `requirements-dev.txt` for development tools

### Blockchain Project Specific Risks
- **Cryptography Library Security** - pysui-fastcrypto, betterproto2
- **Network Communication** - httpx, websockets, gRPC (via betterproto2)
- **Serialization** - canoser, PyYAML
- **Data Handling** - dataclasses_json, jsonschema
- **Protocol Buffers** - betterproto2[grpclib]
- **GraphQL Client** - gql[httpx,websockets]
- **Encoding** - base58
- **Versioning** - setuptools-scm for dynamic versioning

## Excluding Unnecessary Checks

For test files or example code, certain checks can be excluded:

#### Bandit Exclusions

```bash
# Exclude test directories
bandit -r pysui/ --exclude tests/,samples/

# Exclude specific checks
bandit -r pysui/ --skip B101,B601
```

#### pip-audit Exclusions

```bash
# Scan only specific requirements files
pip-audit --requirement requirements.txt --requirement requirements-dev.txt

# Skip editable installs
pip-audit --skip-editable

# Exclude specific packages (use with caution)
pip-audit --ignore-vuln PYSEC-2023-123

# Use custom policy file
pip-audit --policy custom-policy.toml

# Focus on specific dependency type
pip-audit --requirement requirements.txt  # Runtime deps only
pip-audit --requirement requirements-dev.txt  # Dev deps only
```

## Reporting Security Issues

When security vulnerabilities are discovered:
- Report using GitHub Issues
- Mark as security-related issue
- Avoid detailed vulnerability descriptions in public discussions

## Additional Resources

### 🛠️ Tool Documentation
- [Bandit Official Documentation](https://bandit.readthedocs.io/)
- [pip-audit Official Documentation](https://pip.pypa.io/en/stable/topics/pip-audit/)
- [pip-audit GitHub](https://github.com/trailofbits/pip-audit)

### 📚 Security Resources
- [Python Security Best Practices](https://docs.python.org/3/library/security.html)
- [OWASP Python Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Python_Security_Cheat_Sheet.html)
- [Blockchain Security Best Practices](https://owasp.org/www-project-smart-contract-security-standards/)