import pytest
from datetime import datetime
from app import create_app
from app.models import db, User, UserRole
from app.auth_service import AuthService
from app.security import verify_password

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
def client(app):
    """Create test client."""
    return app.test_client()

@pytest.fixture
def app_context(app):
    """Create application context."""
    with app.app_context():
        yield

class TestAuthService:
    """Test cases for AuthService."""
    
    def test_register_user_success(self, app_context):
        """Test successful user registration."""
        result = AuthService.register_user(
            username='testuser',
            email='test@example.com',
            phone='+1234567890',
            password='SecurePass123',
            full_name='Test User'
        )
        
        assert result['success'] is True
        assert result['username'] == 'testuser'
        assert result['email'] == 'test@example.com'
        assert result['role'] == 'customer'
        
        # Verify user was created in database
        user = User.query.filter_by(username='testuser').first()
        assert user is not None
        assert user.email == 'test@example.com'
    
    def test_register_user_duplicate_username(self, app_context):
        """Test registration with duplicate username."""
        AuthService.register_user(
            username='testuser',
            email='test1@example.com',
            phone='+1234567890',
            password='SecurePass123',
            full_name='Test User'
        )
        
        with pytest.raises(ValueError, match='Username or email already exists'):
            AuthService.register_user(
                username='testuser',
                email='test2@example.com',
                phone='+1234567890',
                password='SecurePass123',
                full_name='Another User'
            )
    
    def test_register_user_duplicate_email(self, app_context):
        """Test registration with duplicate email."""
        AuthService.register_user(
            username='testuser1',
            email='test@example.com',
            phone='+1234567890',
            password='SecurePass123',
            full_name='Test User'
        )
        
        with pytest.raises(ValueError, match='Username or email already exists'):
            AuthService.register_user(
                username='testuser2',
                email='test@example.com',
                phone='+1234567890',
                password='SecurePass123',
                full_name='Another User'
            )
    
    def test_register_user_invalid_email(self, app_context):
        """Test registration with invalid email."""
        with pytest.raises(ValueError, match='Invalid email format'):
            AuthService.register_user(
                username='testuser',
                email='invalid-email',
                phone='+1234567890',
                password='SecurePass123',
                full_name='Test User'
            )
    
    def test_register_user_invalid_phone(self, app_context):
        """Test registration with invalid phone."""
        with pytest.raises(ValueError, match='Invalid phone format'):
            AuthService.register_user(
                username='testuser',
                email='test@example.com',
                phone='invalid',
                password='SecurePass123',
                full_name='Test User'
            )
    
    def test_register_user_short_password(self, app_context):
        """Test registration with short password."""
        with pytest.raises(ValueError, match='Password must be at least 8 characters'):
            AuthService.register_user(
                username='testuser',
                email='test@example.com',
                phone='+1234567890',
                password='short',
                full_name='Test User'
            )
    
    def test_register_user_short_username(self, app_context):
        """Test registration with short username."""
        with pytest.raises(ValueError, match='Username must be at least 3 characters'):
            AuthService.register_user(
                username='ab',
                email='test@example.com',
                phone='+1234567890',
                password='SecurePass123',
                full_name='Test User'
            )
    
    def test_login_success(self, app_context):
        """Test successful login."""
        AuthService.register_user(
            username='testuser',
            email='test@example.com',
            phone='+1234567890',
            password='SecurePass123',
            full_name='Test User'
        )
        
        result = AuthService.login('testuser', 'SecurePass123')
        
        assert result['success'] is True
        assert 'access_token' in result
        assert 'refresh_token' in result
        assert result['username'] == 'testuser'
        assert result['role'] == 'customer'
    
    def test_login_invalid_username(self, app_context):
        """Test login with invalid username."""
        with pytest.raises(ValueError, match='Invalid username or password'):
            AuthService.login('nonexistent', 'password')
    
    def test_login_invalid_password(self, app_context):
        """Test login with invalid password."""
        AuthService.register_user(
            username='testuser',
            email='test@example.com',
            phone='+1234567890',
            password='SecurePass123',
            full_name='Test User'
        )
        
        with pytest.raises(ValueError, match='Invalid username or password'):
            AuthService.login('testuser', 'WrongPassword')
    
    def test_login_account_lockout(self, app_context):
        """Test account lockout after multiple failed login attempts."""
        AuthService.register_user(
            username='testuser',
            email='test@example.com',
            phone='+1234567890',
            password='SecurePass123',
            full_name='Test User'
        )
        
        # Try to login 5 times with wrong password
        for i in range(5):
            with pytest.raises(ValueError):
                AuthService.login('testuser', 'WrongPassword')
        
        # Next login attempt should fail with account locked message
        with pytest.raises(ValueError, match='Too many failed login attempts'):
            AuthService.login('testuser', 'SecurePass123')
    
    def test_change_password_success(self, app_context):
        """Test successful password change."""
        AuthService.register_user(
            username='testuser',
            email='test@example.com',
            phone='+1234567890',
            password='SecurePass123',
            full_name='Test User'
        )
        
        user = User.query.filter_by(username='testuser').first()
        
        result = AuthService.change_password(
            user_id=user.id,
            old_password='SecurePass123',
            new_password='NewPassword456'
        )
        
        assert result['success'] is True
        
        # Verify old password no longer works
        with pytest.raises(ValueError):
            AuthService.login('testuser', 'SecurePass123')
        
        # Verify new password works
        result = AuthService.login('testuser', 'NewPassword456')
        assert result['success'] is True
    
    def test_change_password_invalid_old_password(self, app_context):
        """Test password change with invalid old password."""
        AuthService.register_user(
            username='testuser',
            email='test@example.com',
            phone='+1234567890',
            password='SecurePass123',
            full_name='Test User'
        )
        
        user = User.query.filter_by(username='testuser').first()
        
        with pytest.raises(ValueError, match='Invalid current password'):
            AuthService.change_password(
                user_id=user.id,
                old_password='WrongPassword',
                new_password='NewPassword456'
            )
    
    def test_change_password_same_as_old(self, app_context):
        """Test password change with same password as old."""
        AuthService.register_user(
            username='testuser',
            email='test@example.com',
            phone='+1234567890',
            password='SecurePass123',
            full_name='Test User'
        )
        
        user = User.query.filter_by(username='testuser').first()
        
        with pytest.raises(ValueError, match='New password must be different'):
            AuthService.change_password(
                user_id=user.id,
                old_password='SecurePass123',
                new_password='SecurePass123'
            )
    
    def test_get_user_success(self, app_context):
        """Test getting user information."""
        AuthService.register_user(
            username='testuser',
            email='test@example.com',
            phone='+1234567890',
            password='SecurePass123',
            full_name='Test User'
        )
        
        user = User.query.filter_by(username='testuser').first()
        result = AuthService.get_user(user.id)
        
        assert result['username'] == 'testuser'
        assert result['email'] == 'test@example.com'
        assert result['full_name'] == 'Test User'
        assert result['role'] == 'customer'
    
    def test_get_user_not_found(self, app_context):
        """Test getting non-existent user."""
        with pytest.raises(ValueError, match='User not found'):
            AuthService.get_user(999)
    
    def test_update_profile_success(self, app_context):
        """Test successful profile update."""
        AuthService.register_user(
            username='testuser',
            email='test@example.com',
            phone='+1234567890',
            password='SecurePass123',
            full_name='Test User'
        )
        
        user = User.query.filter_by(username='testuser').first()
        
        result = AuthService.update_profile(
            user_id=user.id,
            email='newemail@example.com',
            phone='+9876543210',
            full_name='Updated Name'
        )
        
        assert result['success'] is True
        assert result['email'] == 'newemail@example.com'
        assert result['phone'] == '+9876543210'
        assert result['full_name'] == 'Updated Name'
    
    def test_update_profile_invalid_email(self, app_context):
        """Test profile update with invalid email."""
        AuthService.register_user(
            username='testuser',
            email='test@example.com',
            phone='+1234567890',
            password='SecurePass123',
            full_name='Test User'
        )
        
        user = User.query.filter_by(username='testuser').first()
        
        with pytest.raises(ValueError, match='Invalid email format'):
            AuthService.update_profile(
                user_id=user.id,
                email='invalid-email'
            )
    
    def test_update_profile_duplicate_email(self, app_context):
        """Test profile update with duplicate email."""
        AuthService.register_user(
            username='testuser1',
            email='test1@example.com',
            phone='+1234567890',
            password='SecurePass123',
            full_name='Test User 1'
        )
        
        AuthService.register_user(
            username='testuser2',
            email='test2@example.com',
            phone='+1234567890',
            password='SecurePass123',
            full_name='Test User 2'
        )
        
        user1 = User.query.filter_by(username='testuser1').first()
        
        with pytest.raises(ValueError, match='Email already in use'):
            AuthService.update_profile(
                user_id=user1.id,
                email='test2@example.com'
            )
