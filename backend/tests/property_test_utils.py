"""
Property-Based Testing Utilities
Provides common strategies and helpers for Hypothesis tests
Requirements: 6.3 - Set up property-based testing
"""

from hypothesis import strategies as st, settings, Verbosity
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant
from datetime import datetime, timedelta
import string


# ==================== Settings ====================

# Default settings for property tests
default_settings = settings(
    max_examples=100,  # Run 100 test cases
    verbosity=Verbosity.verbose,
    deadline=None,  # No deadline for slow tests
    print_blob=True  # Print failing examples
)

# Fast settings for quick tests
fast_settings = settings(
    max_examples=20,
    verbosity=Verbosity.normal,
    deadline=1000  # 1 second deadline
)

# Thorough settings for critical tests
thorough_settings = settings(
    max_examples=1000,
    verbosity=Verbosity.verbose,
    deadline=None
)


# ==================== Custom Strategies ====================

# Email addresses
def email_strategy():
    """Generate valid email addresses"""
    username = st.text(
        alphabet=string.ascii_lowercase + string.digits + '._-',
        min_size=1,
        max_size=64
    ).filter(lambda x: x[0] not in '.-' and x[-1] not in '.-')
    
    domain = st.text(
        alphabet=string.ascii_lowercase + string.digits + '-',
        min_size=1,
        max_size=63
    ).filter(lambda x: x[0] != '-' and x[-1] != '-')
    
    tld = st.sampled_from(['com', 'org', 'net', 'edu', 'gov'])
    
    return st.builds(
        lambda u, d, t: f"{u}@{d}.{t}",
        username, domain, tld
    )


# Passwords
def password_strategy(min_length=8, max_length=100):
    """Generate valid passwords"""
    return st.text(
        alphabet=string.ascii_letters + string.digits + string.punctuation,
        min_size=min_length,
        max_size=max_length
    )


# Topics
def topic_strategy(min_length=1, max_length=200):
    """Generate valid topic strings"""
    return st.text(
        alphabet=string.ascii_letters + string.digits + ' -.,()!?&',
        min_size=min_length,
        max_size=max_length
    ).filter(lambda x: x.strip() != '')


# Subtopics arrays
def subtopics_strategy(min_items=1, max_items=20):
    """Generate valid subtopics arrays"""
    return st.lists(
        topic_strategy(min_length=1, max_length=100),
        min_size=min_items,
        max_size=max_items,
        unique=True
    )


# JWT tokens
def jwt_token_strategy():
    """Generate JWT-like tokens"""
    header = st.text(alphabet=string.ascii_letters + string.digits, min_size=20, max_size=50)
    payload = st.text(alphabet=string.ascii_letters + string.digits, min_size=50, max_size=200)
    signature = st.text(alphabet=string.ascii_letters + string.digits, min_size=20, max_size=50)
    
    return st.builds(
        lambda h, p, s: f"{h}.{p}.{s}",
        header, payload, signature
    )


# API keys
def api_key_strategy(prefix='sk_'):
    """Generate API key strings"""
    key_part = st.text(
        alphabet=string.ascii_letters + string.digits,
        min_size=32,
        max_size=64
    )
    return st.builds(lambda k: f"{prefix}{k}", key_part)


# Timestamps
def timestamp_strategy(min_year=2020, max_year=2030):
    """Generate datetime objects"""
    return st.datetimes(
        min_value=datetime(min_year, 1, 1),
        max_value=datetime(max_year, 12, 31)
    )


# File sizes
def file_size_strategy(min_size=0, max_size=10*1024*1024):
    """Generate file sizes in bytes"""
    return st.integers(min_value=min_size, max_value=max_size)


# File extensions
def file_extension_strategy(allowed_only=True):
    """Generate file extensions"""
    if allowed_only:
        return st.sampled_from(['jpg', 'jpeg', 'png', 'gif', 'webp'])
    else:
        return st.text(
            alphabet=string.ascii_lowercase,
            min_size=2,
            max_size=5
        )


# HTTP status codes
def http_status_strategy():
    """Generate HTTP status codes"""
    return st.sampled_from([
        200, 201, 204,  # Success
        400, 401, 403, 404, 422, 429,  # Client errors
        500, 502, 503, 504  # Server errors
    ])


# User roles
def role_strategy():
    """Generate user roles"""
    return st.sampled_from(['user', 'admin', 'moderator'])


# Quota tiers
def quota_tier_strategy():
    """Generate quota tiers"""
    return st.sampled_from(['free', 'basic', 'premium', 'enterprise'])


# IP addresses
def ip_address_strategy():
    """Generate IP addresses"""
    octet = st.integers(min_value=0, max_value=255)
    return st.builds(
        lambda a, b, c, d: f"{a}.{b}.{c}.{d}",
        octet, octet, octet, octet
    )


# User agents
def user_agent_strategy():
    """Generate user agent strings"""
    browsers = ['Chrome', 'Firefox', 'Safari', 'Edge']
    versions = st.integers(min_value=80, max_value=120)
    
    return st.builds(
        lambda b, v: f"Mozilla/5.0 ({b}/{v})",
        st.sampled_from(browsers),
        versions
    )


# ==================== Composite Strategies ====================

def user_data_strategy():
    """Generate complete user data"""
    return st.fixed_dictionaries({
        'email': email_strategy(),
        'password': password_strategy(),
        'role': role_strategy(),
        'quota_tier': quota_tier_strategy(),
        'created_at': timestamp_strategy()
    })


def session_data_strategy():
    """Generate complete session data"""
    return st.fixed_dictionaries({
        'token': jwt_token_strategy(),
        'user_id': st.integers(min_value=1, max_value=1000000),
        'expires_at': timestamp_strategy(),
        'ip_address': ip_address_strategy(),
        'user_agent': user_agent_strategy()
    })


def api_key_data_strategy():
    """Generate complete API key data"""
    return st.fixed_dictionaries({
        'key': api_key_strategy(),
        'user_id': st.integers(min_value=1, max_value=1000000),
        'name': st.text(min_size=1, max_size=100),
        'created_at': timestamp_strategy()
    })


# ==================== Helper Functions ====================

def is_valid_email(email):
    """Check if email is valid"""
    import re
    pattern = r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_password(password, min_length=8):
    """Check if password meets requirements"""
    return len(password) >= min_length


def is_valid_topic(topic, max_length=200):
    """Check if topic is valid"""
    return 0 < len(topic.strip()) <= max_length


def is_valid_jwt(token):
    """Check if JWT format is valid"""
    parts = token.split('.')
    return len(parts) == 3 and all(len(p) > 0 for p in parts)


def is_valid_api_key(key, prefix='sk_'):
    """Check if API key format is valid"""
    return key.startswith(prefix) and len(key) > len(prefix) + 20


# ==================== State Machine Base ====================

class AuthStateMachine(RuleBasedStateMachine):
    """
    State machine for testing authentication flows
    Example of stateful property-based testing
    """
    
    def __init__(self):
        super().__init__()
        self.users = {}
        self.sessions = {}
        self.api_keys = {}
    
    @rule(email=email_strategy(), password=password_strategy())
    def register_user(self, email, password):
        """Register a new user"""
        if email not in self.users:
            self.users[email] = {
                'password': password,
                'role': 'user',
                'created_at': datetime.utcnow()
            }
    
    @rule(email=email_strategy(), password=password_strategy())
    def login_user(self, email, password):
        """Login a user"""
        if email in self.users and self.users[email]['password'] == password:
            token = f"token_{len(self.sessions)}"
            self.sessions[token] = {
                'email': email,
                'expires_at': datetime.utcnow() + timedelta(hours=24)
            }
    
    @invariant()
    def sessions_not_expired(self):
        """All sessions should not be expired"""
        now = datetime.utcnow()
        for token, session in self.sessions.items():
            # In real test, we'd check expiration
            pass


# ==================== Example Property Tests ====================

def example_password_property():
    """
    Example property test for password hashing
    This is a template - actual tests are in test files
    """
    from hypothesis import given
    
    @given(password=password_strategy())
    def test_password_hashing_roundtrip(password):
        # This would use actual PasswordHasher
        # hashed = hasher.hash(password)
        # assert hasher.verify(password, hashed)
        pass


def example_topic_property():
    """
    Example property test for topic validation
    This is a template - actual tests are in test files
    """
    from hypothesis import given
    
    @given(topic=topic_strategy())
    def test_topic_validation(topic):
        # This would use actual validator
        # result = validator.validate_topic(topic)
        # assert result.is_valid
        pass
