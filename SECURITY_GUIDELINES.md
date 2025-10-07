# PySui Security Guidelines

## 🔒 Security Scanning Tools

PySui project uses dual security scanning tools:
- **Bandit** - Python code security analysis
- **Snyk** - Dependency vulnerability scanning + License compliance

## Quick Start

```bash
# Install development dependencies (includes both security tools)
pip install -r requirements-dev.txt

# Run code security scanning (Bandit)
bandit -r pysui/ --severity-level medium

# Run dependency security scanning (Snyk)
snyk test
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

### 🔗 Snyk (Dependency Security)

```bash
# First-time authentication required
snyk auth [token]

# Scan dependency vulnerabilities
snyk test

# Scan all projects (if multiple)
snyk test --all-projects

# Generate detailed report
snyk test --json > snyk-report.json

# Check license compliance
snyk test --license-check
```

### 🔄 Combined Scanning

```bash
# Complete security scan (code + dependencies)
bandit -r pysui/ --severity-level medium
snyk test --license-check
```

## Common Security Issues

### 🐍 Bandit Detected Issues

1. **Private Key Management** - Hardcoded private keys, insecure key storage
2. **Dynamic Code Execution** - Use of exec() and eval()
3. **Network Communication** - SSL/TLS configuration issues
4. **Cryptographic Operations** - Insecure hash algorithms, random number generation

### 🔗 Snyk Detected Issues

1. **Dependency Vulnerabilities** - Security vulnerabilities in third-party libraries
2. **License Compliance** - Open source license conflicts
3. **Outdated Versions** - Known vulnerabilities in old versions
4. **Supply Chain Security** - Security issues in dependencies of dependencies

## Special Focus for PySui

**Blockchain Project Specific Risks**:
- **Cryptography Library Security** - pysui-fastcrypto, betterproto2
- **Network Communication** - httpx, websockets, gRPC
- **Serialization** - canoser, PyYAML
- **Configuration Management** - Sensitive information storage

## Excluding Unnecessary Checks

For test files or example code, certain checks can be excluded:

#### Bandit Exclusions

```bash
# Exclude test directories
bandit -r pysui/ --exclude tests/,samples/

# Exclude specific checks
bandit -r pysui/ --skip B101,B601
```

#### Snyk Exclusions

```bash
# Exclude development dependencies
snyk test --exclude=dev

# Ignore specific vulnerabilities (use with caution)
snyk test --exclude=SNYK-PYTHON-PYYAML-590148
```

## Reporting Security Issues

When security vulnerabilities are discovered:
- Report using GitHub Issues
- Mark as security-related issue
- Avoid detailed vulnerability descriptions in public discussions

## Additional Resources

### 🛠️ Tool Documentation
- [Bandit Official Documentation](https://bandit.readthedocs.io/)
- [Snyk Official Documentation](https://support.snyk.io/)
- [Snyk CLI Guide](https://docs.snyk.io/snyk-cli/)

### 📚 Security Resources
- [Python Security Best Practices](https://docs.python.org/3/library/security.html)
- [OWASP Python Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Python_Security_Cheat_Sheet.html)
- [Blockchain Security Best Practices](https://owasp.org/www-project-smart-contract-security-standards/)