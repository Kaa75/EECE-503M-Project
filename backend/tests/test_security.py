import pytest
from app import create_app
from app.models import db, User
from app.security import (
    hash_password, verify_password, generate_account_number,
    sanitize_input, validate_email, validate_phone, 
    check_account_lockout, lock_account, unlock_account
)
from datetime import datetime, timedelta

@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def app_context(app):
    """Create application context."""
    with app.app_context():
        yield

class TestSecurityFunctions:
    """Test cases for security utility functions."""
    
    def test_hash_password_success(self, app_context):
        """Test successful password hashing."""
        password = 'SecurePassword123'
        hashed = hash_password(password)
        
        assert hashed != password
        assert len(hashed) > 20
    
    def test_hash_password_short(self, app_context):
        """Test hashing short password."""
        with pytest.raises(ValueError, match='Password must be at least 8 characters'):
            hash_password('short')
    
    def test_hash_password_empty(self, app_context):
        """Test hashing empty password."""
        with pytest.raises(ValueError, match='Password must be at least 8 characters'):
            hash_password('')
    
    def test_verify_password_success(self, app_context):
        """Test successful password verification."""
        password = 'SecurePassword123'
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self, app_context):
        """Test verification with incorrect password."""
        password = 'SecurePassword123'
        hashed = hash_password(password)
        
        assert verify_password('WrongPassword', hashed) is False
    
    def test_verify_password_invalid_hash(self, app_context):
        """Test verification with invalid hash."""
        assert verify_password('password', 'invalid_hash') is False
    
    def test_generate_account_number(self, app_context):
        """Test account number generation."""
        account_number = generate_account_number()
        
        assert account_number.startswith('ACC-')
        assert len(account_number) == 14  # ACC- + 10 digits
        assert account_number[4:].isdigit()
    
    def test_generate_account_number_uniqueness(self, app_context):
        """Test that generated account numbers are unique."""
        numbers = set()
        
        for _ in range(100):
            numbers.add(generate_account_number())
        
        assert len(numbers) == 100
    
    def test_sanitize_input_removes_sql_injection(self, app_context):
        """Test sanitization removes SQL injection attempts."""
        malicious = "'; DROP TABLE users; --"
        sanitized = sanitize_input(malicious)
        
        assert "DROP TABLE" not in sanitized
        assert "--" not in sanitized
    
    def test_sanitize_input_removes_script_tags(self, app_context):
        """Test sanitization removes script tags."""
        malicious = "<script>alert('xss')</script>"
        sanitized = sanitize_input(malicious)
        
        assert "<script>" not in sanitized
        assert "</script>" not in sanitized
    
    def test_sanitize_input_respects_max_length(self, app_context):
        """Test sanitization respects max length."""
        long_input = "a" * 500
        sanitized = sanitize_input(long_input, max_length=100)
        
        assert len(sanitized) <= 100
    
    def test_sanitize_input_strips_whitespace(self, app_context):
        """Test sanitization strips whitespace."""
        input_with_spaces = "  test input  "
        sanitized = sanitize_input(input_with_spaces)
        
        assert sanitized == "test input"
    
    def test_validate_email_valid(self, app_context):
        """Test email validation with valid email."""
        assert validate_email('user@example.com') is True
        assert validate_email('test.user@example.co.uk') is True
        assert validate_email('user+tag@example.com') is True
    
    def test_validate_email_invalid(self, app_context):
        """Test email validation with invalid email."""
        assert validate_email('invalid-email') is False
        assert validate_email('user@') is False
        assert validate_email('@example.com') is False
        assert validate_email('user@.com') is False
    
    def test_validate_phone_valid(self, app_context):
        """Test phone validation with valid phone."""
        assert validate_phone('+1234567890') is True
        assert validate_phone('1234567890') is True
        assert validate_phone('+1 234 567 8900') is False  # spaces not allowed
    
    def test_validate_phone_invalid(self, app_context):
        """Test phone validation with invalid phone."""
        assert validate_phone('invalid') is False
        assert validate_phone('123') is False
        assert validate_phone('') is False
    
    def test_check_account_lockout_not_locked(self, app_context):
        """Test checking lockout status of non-locked account."""
        user = User(
            username='testuser',
            email='test@example.com',
            phone='+1234567890',
            password_hash='hash',
            full_name='Test User'
        )
        db.session.add(user)
        db.session.commit()
        
        assert check_account_lockout(user) is False
    
    def test_check_account_lockout_locked(self, app_context):
        """Test checking lockout status of locked account."""
        user = User(
            username='testuser',
            email='test@example.com',
            phone='+1234567890',
            password_hash='hash',
            full_name='Test User',
            locked_until=datetime.utcnow() + timedelta(minutes=15)
        )
        db.session.add(user)
        db.session.commit()
        
        assert check_account_lockout(user) is True
    
    def test_check_account_lockout_expired(self, app_context):
        """Test checking lockout status of expired lock."""
        user = User(
            username='testuser',
            email='test@example.com',
            phone='+1234567890',
            password_hash='hash',
            full_name='Test User',
            locked_until=datetime.utcnow() - timedelta(minutes=1)
        )
        db.session.add(user)
        db.session.commit()
        
        assert check_account_lockout(user) is False
    
    def test_lock_account_success(self, app_context):
        """Test successful account locking."""
        user = User(
            username='testuser',
            email='test@example.com',
            phone='+1234567890',
            password_hash='hash',
            full_name='Test User',
            failed_login_attempts=5
        )
        db.session.add(user)
        db.session.commit()
        
        lock_account(user, duration_minutes=15)
        
        assert user.locked_until is not None
        assert user.failed_login_attempts == 0
        assert check_account_lockout(user) is True
    
    def test_unlock_account_success(self, app_context):
        """Test successful account unlocking."""
        user = User(
            username='testuser',
            email='test@example.com',
            phone='+1234567890',
            password_hash='hash',
            full_name='Test User',
            locked_until=datetime.utcnow() + timedelta(minutes=15),
            failed_login_attempts=5
        )
        db.session.add(user)
        db.session.commit()
        
        unlock_account(user)
        
        assert user.locked_until is None
        assert user.failed_login_attempts == 0
        assert check_account_lockout(user) is False
    
    def test_password_hashing_different_salts(self, app_context):
        """Test that same password produces different hashes (different salts)."""
        password = 'SecurePassword123'
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        assert hash1 != hash2
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True
    
    def test_sanitize_input_preserves_safe_characters(self, app_context):
        """Test that sanitization preserves safe characters."""
        safe_input = "John Doe's Account (123)"
        sanitized = sanitize_input(safe_input)
        
        assert "John" in sanitized
        assert "Doe" in sanitized
        assert "Account" in sanitized
        assert "123" in sanitized
