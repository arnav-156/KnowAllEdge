#!/bin/bash
# Security Testing Script
# Requirements: 6.7 - Set up security testing tools

echo "========================================="
echo "Running Security Tests"
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Exit on error
set -e

# 1. Bandit - Python Security Scanner
echo -e "\n${YELLOW}1. Running Bandit (Python Security Scanner)...${NC}"
if command -v bandit &> /dev/null; then
    bandit -r . -c .bandit -f json -o bandit-report.json
    bandit -r . -c .bandit
    echo -e "${GREEN}✓ Bandit scan complete${NC}"
else
    echo -e "${RED}✗ Bandit not installed. Install with: pip install bandit${NC}"
fi

# 2. Safety - Dependency Vulnerability Scanner
echo -e "\n${YELLOW}2. Running Safety (Dependency Scanner)...${NC}"
if command -v safety &> /dev/null; then
    safety check --json --output safety-report.json || true
    safety check
    echo -e "${GREEN}✓ Safety scan complete${NC}"
else
    echo -e "${RED}✗ Safety not installed. Install with: pip install safety${NC}"
fi

# 3. Pip-audit - Alternative Dependency Scanner
echo -e "\n${YELLOW}3. Running pip-audit...${NC}"
if command -v pip-audit &> /dev/null; then
    pip-audit --format json --output pip-audit-report.json || true
    pip-audit
    echo -e "${GREEN}✓ Pip-audit scan complete${NC}"
else
    echo -e "${RED}✗ pip-audit not installed. Install with: pip install pip-audit${NC}"
fi

# 4. Check for hardcoded secrets
echo -e "\n${YELLOW}4. Checking for hardcoded secrets...${NC}"
if command -v detect-secrets &> /dev/null; then
    detect-secrets scan --baseline .secrets.baseline
    echo -e "${GREEN}✓ Secret scan complete${NC}"
else
    echo -e "${RED}✗ detect-secrets not installed. Install with: pip install detect-secrets${NC}"
fi

# 5. Check SSL/TLS configuration
echo -e "\n${YELLOW}5. Checking SSL/TLS configuration...${NC}"
python3 << 'EOF'
import ssl
import sys

# Check SSL version
print(f"SSL Version: {ssl.OPENSSL_VERSION}")

# Check for weak ciphers
context = ssl.create_default_context()
print(f"Default ciphers: {context.get_ciphers()[:3]}...")  # Show first 3

# Verify TLS 1.2+ is available
try:
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    print("✓ TLS 1.2+ is available")
except:
    print("✗ TLS 1.2+ is NOT available")
    sys.exit(1)
EOF
echo -e "${GREEN}✓ SSL/TLS check complete${NC}"

# 6. Check for common security misconfigurations
echo -e "\n${YELLOW}6. Checking for security misconfigurations...${NC}"
python3 << 'EOF'
import os
import sys

issues = []

# Check DEBUG mode
if os.getenv('FLASK_DEBUG', 'false').lower() == 'true':
    issues.append("⚠ DEBUG mode is enabled")

# Check SECRET_KEY
if not os.getenv('SECRET_KEY'):
    issues.append("⚠ SECRET_KEY is not set")

# Check HTTPS enforcement
if os.getenv('FORCE_HTTPS', 'true').lower() != 'true':
    issues.append("⚠ HTTPS enforcement is disabled")

if issues:
    print("\n".join(issues))
    sys.exit(1)
else:
    print("✓ No security misconfigurations found")
EOF
echo -e "${GREEN}✓ Configuration check complete${NC}"

# Summary
echo -e "\n========================================="
echo -e "${GREEN}Security Testing Complete!${NC}"
echo "========================================="
echo "Reports generated:"
echo "  - bandit-report.json"
echo "  - safety-report.json"
echo "  - pip-audit-report.json"
echo ""
echo "Review the reports for any security issues."
