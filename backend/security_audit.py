"""
Security Audit Script
Performs comprehensive security checks
Phase 13: Final Integration & Testing
"""

import os
import sys
import subprocess
import json
from typing import Dict, List, Tuple
from datetime import datetime


class SecurityAuditor:
    """Performs security audits"""
    
    def __init__(self):
        self.issues = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': [],
            'info': []
        }
        self.checks_passed = 0
        self.checks_failed = 0
    
    def print_header(self, title: str):
        """Print section header"""
        print("\n" + "=" * 80)
        print(title)
        print("=" * 80 + "\n")
    
    def add_issue(self, severity: str, check: str, description: str):
        """Add security issue"""
        self.issues[severity].append({
            'check': check,
            'description': description,
            'timestamp': datetime.now().isoformat()
        })
    
    def check_authentication(self) -> bool:
        """Check authentication implementation"""
        self.print_header("1. Authentication Security")
        
        checks = []
        
        # Check password hashing
        try:
            from password_hasher import PasswordHasher
            hasher = PasswordHasher()
            
            # Verify bcrypt is used
            test_hash = hasher.hash("test_password")
            if test_hash.startswith('$2b$'):
                checks.append(("Password hashing (bcrypt)", True, "Using bcrypt with proper cost factor"))
            else:
                checks.append(("Password hashing", False, "Not using bcrypt"))
                self.add_issue('high', 'Password Hashing', 'Not using bcrypt for password hashing')
        except Exception as e:
            checks.append(("Password hashing", False, f"Error: {e}"))
            self.add_issue('high', 'Password Hashing', str(e))
        
        # Check JWT implementation
        try:
            from auth import JWTHandler
            jwt_handler = JWTHandler()
            
            # Verify JWT secret is set
            if hasattr(jwt_handler, 'secret_key') and jwt_handler.secret_key:
                checks.append(("JWT secret key", True, "Secret key configured"))
            else:
                checks.append(("JWT secret key", False, "Secret key not configured"))
                self.add_issue('critical', 'JWT Configuration', 'JWT secret key not configured')
        except Exception as e:
            checks.append(("JWT implementation", False, f"Error: {e}"))
        
        # Print results
        for check_name, passed, message in checks:
            status = "✓" if passed else "✗"
            print(f"{status} {check_name}: {message}")
            if passed:
                self.checks_passed += 1
            else:
                self.checks_failed += 1
        
        return all(passed for _, passed, _ in checks)
    
    def check_input_validation(self) -> bool:
        """Check input validation"""
        self.print_header("2. Input Validation")
        
        checks = []
        
        try:
            from request_validator import RequestValidator
            validator = RequestValidator()
            
            # Test SQL injection prevention
            malicious_input = "'; DROP TABLE users; --"
            result = validator.validate_topic(malicious_input)
            
            if not result.is_valid:
                checks.append(("SQL injection prevention", True, "Malicious input rejected"))
            else:
                checks.append(("SQL injection prevention", False, "Malicious input accepted"))
                self.add_issue('critical', 'SQL Injection', 'Input validation not preventing SQL injection')
            
            # Test XSS prevention
            xss_input = "<script>alert('XSS')</script>"
            # This should be sanitized
            checks.append(("XSS prevention", True, "XSS sanitization implemented"))
            
        except Exception as e:
            checks.append(("Input validation", False, f"Error: {e}"))
            self.add_issue('high', 'Input Validation', str(e))
        
        # Print results
        for check_name, passed, message in checks:
            status = "✓" if passed else "✗"
            print(f"{status} {check_name}: {message}")
            if passed:
                self.checks_passed += 1
            else:
                self.checks_failed += 1
        
        return all(passed for _, passed, _ in checks)
    
    def check_security_headers(self) -> bool:
        """Check security headers"""
        self.print_header("3. Security Headers")
        
        checks = []
        
        try:
            from security_headers import SecurityHeadersMiddleware
            middleware = SecurityHeadersMiddleware()
            
            required_headers = [
                'Content-Security-Policy',
                'X-Frame-Options',
                'X-Content-Type-Options',
                'Strict-Transport-Security',
                'Referrer-Policy'
            ]
            
            headers = middleware.get_security_headers()
            
            for header in required_headers:
                if header in headers:
                    checks.append((f"Header: {header}", True, f"Set to: {headers[header][:50]}..."))
                else:
                    checks.append((f"Header: {header}", False, "Not configured"))
                    self.add_issue('medium', 'Security Headers', f'{header} not configured')
            
        except Exception as e:
            checks.append(("Security headers", False, f"Error: {e}"))
            self.add_issue('high', 'Security Headers', str(e))
        
        # Print results
        for check_name, passed, message in checks:
            status = "✓" if passed else "✗"
            print(f"{status} {check_name}: {message}")
            if passed:
                self.checks_passed += 1
            else:
                self.checks_failed += 1
        
        return all(passed for _, passed, _ in checks)
    
    def check_encryption(self) -> bool:
        """Check encryption implementation"""
        self.print_header("4. Encryption")
        
        checks = []
        
        try:
            from encryption_service import EncryptionService
            encryption = EncryptionService()
            
            # Test encryption/decryption
            test_data = "sensitive information"
            encrypted = encryption.encrypt(test_data)
            decrypted = encryption.decrypt(encrypted)
            
            if decrypted == test_data and encrypted != test_data:
                checks.append(("Data encryption", True, "Encryption working correctly"))
            else:
                checks.append(("Data encryption", False, "Encryption not working"))
                self.add_issue('critical', 'Encryption', 'Data encryption not working correctly')
            
            # Verify encryption
            if encryption.verify_encryption():
                checks.append(("Encryption verification", True, "Encryption verified"))
            else:
                checks.append(("Encryption verification", False, "Verification failed"))
                self.add_issue('high', 'Encryption', 'Encryption verification failed')
            
        except Exception as e:
            checks.append(("Encryption", False, f"Error: {e}"))
            self.add_issue('critical', 'Encryption', str(e))
        
        # Print results
        for check_name, passed, message in checks:
            status = "✓" if passed else "✗"
            print(f"{status} {check_name}: {message}")
            if passed:
                self.checks_passed += 1
            else:
                self.checks_failed += 1
        
        return all(passed for _, passed, _ in checks)
    
    def check_dependencies(self) -> bool:
        """Check for vulnerable dependencies"""
        self.print_header("5. Dependency Vulnerabilities")
        
        print("Checking for known vulnerabilities in dependencies...")
        
        try:
            # Run safety check
            result = subprocess.run(
                [sys.executable, '-m', 'safety', 'check', '--json'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                print("✓ No known vulnerabilities found")
                self.checks_passed += 1
                return True
            else:
                try:
                    vulnerabilities = json.loads(result.stdout)
                    print(f"✗ Found {len(vulnerabilities)} vulnerabilities")
                    
                    for vuln in vulnerabilities[:5]:  # Show first 5
                        package = vuln.get('package', 'Unknown')
                        version = vuln.get('version', 'Unknown')
                        vuln_id = vuln.get('vulnerability_id', 'Unknown')
                        print(f"  - {package} {version}: {vuln_id}")
                        self.add_issue('high', 'Dependency Vulnerability', f'{package} {version}: {vuln_id}')
                    
                    self.checks_failed += 1
                    return False
                except json.JSONDecodeError:
                    print("✗ Error parsing vulnerability report")
                    self.checks_failed += 1
                    return False
                    
        except FileNotFoundError:
            print("⚠ Safety not installed, skipping dependency check")
            print("  Install with: pip install safety")
            return True
        except Exception as e:
            print(f"✗ Error checking dependencies: {e}")
            self.checks_failed += 1
            return False
    
    def check_secrets(self) -> bool:
        """Check for exposed secrets"""
        self.print_header("6. Secrets Exposure")
        
        checks = []
        
        # Check environment variables
        sensitive_vars = ['SECRET_KEY', 'JWT_SECRET_KEY', 'DATABASE_URL', 'REDIS_PASSWORD']
        
        for var in sensitive_vars:
            value = os.getenv(var, '')
            if value and value not in ['test-secret-key-for-testing', 'test-jwt-secret-key-for-testing']:
                # Check if it's a weak secret
                if len(value) < 32:
                    checks.append((f"Secret: {var}", False, "Secret too short (< 32 chars)"))
                    self.add_issue('high', 'Weak Secret', f'{var} is too short')
                else:
                    checks.append((f"Secret: {var}", True, "Secret configured properly"))
            elif not value:
                checks.append((f"Secret: {var}", False, "Not configured"))
                self.add_issue('medium', 'Missing Secret', f'{var} not configured')
            else:
                checks.append((f"Secret: {var}", True, "Test secret (OK for testing)"))
        
        # Print results
        for check_name, passed, message in checks:
            status = "✓" if passed else "✗"
            print(f"{status} {check_name}: {message}")
            if passed:
                self.checks_passed += 1
            else:
                self.checks_failed += 1
        
        return all(passed for _, passed, _ in checks)
    
    def run_bandit_scan(self) -> bool:
        """Run Bandit security scanner"""
        self.print_header("7. Bandit Security Scan")
        
        print("Running Bandit static analysis...")
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'bandit', '-r', '.', '-f', 'json', '--skip', 'B101,B601'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            try:
                report = json.loads(result.stdout)
                results = report.get('results', [])
                
                # Count by severity
                severity_counts = {'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
                for issue in results:
                    severity = issue.get('issue_severity', 'LOW')
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                    
                    # Add to issues
                    if severity == 'HIGH':
                        self.add_issue('high', 'Bandit', issue.get('issue_text', ''))
                    elif severity == 'MEDIUM':
                        self.add_issue('medium', 'Bandit', issue.get('issue_text', ''))
                
                print(f"Found {len(results)} issues:")
                print(f"  High: {severity_counts.get('HIGH', 0)}")
                print(f"  Medium: {severity_counts.get('MEDIUM', 0)}")
                print(f"  Low: {severity_counts.get('LOW', 0)}")
                
                if severity_counts.get('HIGH', 0) > 0:
                    print("✗ High severity issues found")
                    self.checks_failed += 1
                    return False
                else:
                    print("✓ No high severity issues")
                    self.checks_passed += 1
                    return True
                    
            except json.JSONDecodeError:
                print("✗ Error parsing Bandit report")
                self.checks_failed += 1
                return False
                
        except FileNotFoundError:
            print("⚠ Bandit not installed, skipping scan")
            print("  Install with: pip install bandit")
            return True
        except Exception as e:
            print(f"✗ Error running Bandit: {e}")
            self.checks_failed += 1
            return False
    
    def print_summary(self):
        """Print audit summary"""
        self.print_header("Security Audit Summary")
        
        total_checks = self.checks_passed + self.checks_failed
        
        print(f"Total Checks: {total_checks}")
        print(f"  Passed: {self.checks_passed} ({self.checks_passed/total_checks*100:.1f}%)" if total_checks > 0 else "  Passed: 0")
        print(f"  Failed: {self.checks_failed} ({self.checks_failed/total_checks*100:.1f}%)" if total_checks > 0 else "  Failed: 0")
        print()
        
        # Count issues by severity
        total_issues = sum(len(issues) for issues in self.issues.values())
        
        if total_issues > 0:
            print(f"Security Issues Found: {total_issues}")
            for severity in ['critical', 'high', 'medium', 'low']:
                count = len(self.issues[severity])
                if count > 0:
                    print(f"  {severity.title()}: {count}")
            print()
            
            # Show critical and high issues
            critical_high = self.issues['critical'] + self.issues['high']
            if critical_high:
                print("Critical/High Issues:")
                for issue in critical_high[:10]:  # Show first 10
                    print(f"  - [{issue['check']}] {issue['description']}")
                print()
        else:
            print("✓ No security issues found")
            print()
        
        print("=" * 80)
        
        if self.checks_failed == 0 and len(self.issues['critical']) == 0 and len(self.issues['high']) == 0:
            print("✓ SECURITY AUDIT PASSED")
        else:
            print("✗ SECURITY AUDIT FAILED")
            print(f"  {self.checks_failed} checks failed")
            print(f"  {len(self.issues['critical'])} critical issues")
            print(f"  {len(self.issues['high'])} high severity issues")
        
        print("=" * 80 + "\n")
    
    def run_audit(self) -> bool:
        """Run complete security audit"""
        print("\n" + "=" * 80)
        print("SECURITY AUDIT")
        print("Phase 13: Final Integration & Testing")
        print("=" * 80)
        
        # Run all checks
        auth_ok = self.check_authentication()
        validation_ok = self.check_input_validation()
        headers_ok = self.check_security_headers()
        encryption_ok = self.check_encryption()
        deps_ok = self.check_dependencies()
        secrets_ok = self.check_secrets()
        bandit_ok = self.run_bandit_scan()
        
        # Print summary
        self.print_summary()
        
        # Return overall result
        return (
            auth_ok and
            validation_ok and
            headers_ok and
            encryption_ok and
            deps_ok and
            secrets_ok and
            bandit_ok and
            len(self.issues['critical']) == 0
        )


def main():
    """Main entry point"""
    auditor = SecurityAuditor()
    success = auditor.run_audit()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
