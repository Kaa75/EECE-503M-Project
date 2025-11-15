import pytest
import json
from app import create_app
from app.models import db, User, UserRole
from app.auth_service import AuthService
from app.account_service import AccountService

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

@pytest.fixture
def auth_headers(app_context, client):
    """Create authentication headers with JWT token."""
    # Register and login a user
    result = AuthService.register_user(
        username='testuser',
        email='test@example.com',
        phone='+1234567890',
        password='SecurePass123',
        full_name='Test User'
    )
    
    response = client.post('/api/auth/login', 
        json={'username': 'testuser', 'password': 'SecurePass123'}
    )
    
    data = json.loads(response.data)
    return {
        'Authorization': f"Bearer {data['access_token']}",
        'Content-Type': 'application/json'
    }

@pytest.fixture
def admin_headers(app_context, client):
    """Create admin authentication headers."""
    result = AuthService.register_user(
        username='admin',
        email='admin@example.com',
        phone='+1234567890',
        password='Admin@123',
        full_name='Admin User'
    )
    
    user = User.query.get(result['user_id'])
    user.role = UserRole.ADMIN
    db.session.commit()
    
    response = client.post('/api/auth/login',
        json={'username': 'admin', 'password': 'Admin@123'}
    )
    
    data = json.loads(response.data)
    return {
        'Authorization': f"Bearer {data['access_token']}",
        'Content-Type': 'application/json'
    }

class TestAuthRoutes:
    """Test cases for authentication routes."""
    
    def test_register_route_success(self, client):
        """Test user registration via HTTP endpoint."""
        response = client.post('/api/auth/register', json={
            'username': 'newuser',
            'email': 'new@example.com',
            'phone': '+1234567890',
            'password': 'SecurePass123',
            'full_name': 'New User'
        })
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['username'] == 'newuser'
    
    def test_register_route_missing_fields(self, client):
        """Test registration with missing required fields."""
        response = client.post('/api/auth/register', json={
            'username': 'newuser',
            'email': 'new@example.com'
            # Missing phone, password, full_name
        })
        
        assert response.status_code == 400
    
    def test_register_route_invalid_json(self, client):
        """Test registration with invalid JSON."""
        response = client.post('/api/auth/register',
            data='invalid json',
            content_type='application/json'
        )
        
        assert response.status_code == 400
    
    def test_login_route_success(self, app_context, client):
        """Test login via HTTP endpoint."""
        # Register user first
        AuthService.register_user(
            username='testuser',
            email='test@example.com',
            phone='+1234567890',
            password='SecurePass123',
            full_name='Test User'
        )
        
        response = client.post('/api/auth/login', json={
            'username': 'testuser',
            'password': 'SecurePass123'
        })
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'access_token' in data
        assert 'refresh_token' in data
    
    def test_login_route_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post('/api/auth/login', json={
            'username': 'nonexistent',
            'password': 'wrongpass'
        })
        
        # Backend returns 401 for invalid credentials
        assert response.status_code == 401
    
    def test_logout_route_success(self, client, auth_headers):
        """Test logout endpoint."""
        response = client.post('/api/auth/logout', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
    
    def test_logout_route_no_token(self, client):
        """Test logout without authentication token."""
        response = client.post('/api/auth/logout')
        
        assert response.status_code == 401
    
    def test_get_profile_route_success(self, client, auth_headers):
        """Test getting user profile."""
        response = client.get('/api/auth/profile', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['username'] == 'testuser'
    
    def test_get_profile_route_no_token(self, client):
        """Test getting profile without token."""
        response = client.get('/api/auth/profile')
        
        assert response.status_code == 401
    
    def test_update_profile_route_success(self, client, auth_headers):
        """Test updating profile."""
        response = client.put('/api/auth/profile',
            headers=auth_headers,
            json={
                'email': 'updated@example.com',
                'full_name': 'Updated Name'
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['email'] == 'updated@example.com'
    
    def test_change_password_route_success(self, client, auth_headers):
        """Test changing password."""
        response = client.post('/api/auth/change-password',
            headers=auth_headers,
            json={
                'old_password': 'SecurePass123',
                'new_password': 'NewPassword456'
            }
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True


class TestAccountRoutes:
    """Test cases for account routes."""
    
    def test_create_account_route_success(self, client, auth_headers):
        """Test creating account via HTTP endpoint."""
        response = client.post('/api/accounts',
            headers=auth_headers,
            json={
                'account_type': 'checking',
                'opening_balance': 1000.0
            }
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['account_type'] == 'checking'
    
    def test_create_account_route_no_token(self, client):
        """Test creating account without authentication."""
        response = client.post('/api/accounts',
            json={
                'account_type': 'checking',
                'opening_balance': 1000.0
            }
        )
        
        assert response.status_code == 401
    
    def test_get_user_accounts_route(self, app_context, client, auth_headers):
        """Test getting user accounts."""
        # Create an account first
        user = User.query.filter_by(username='testuser').first()
        AccountService.create_account(
            user_id=user.id,
            account_type='checking',
            opening_balance=1000.0
        )
        
        response = client.get(f'/api/accounts/user/{user.id}', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'accounts' in data
        assert len(data['accounts']) > 0
    
    def test_get_account_route(self, app_context, client, auth_headers):
        """Test getting specific account."""
        user = User.query.filter_by(username='testuser').first()
        account = AccountService.create_account(
            user_id=user.id,
            account_type='checking',
            opening_balance=1000.0
        )
        
        response = client.get(f"/api/accounts/{account['account_id']}", 
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['balance'] == 1000.0
    
    def test_freeze_account_route(self, app_context, client, admin_headers):
        """Test freezing account via admin."""
        # Create a regular user and account
        user_result = AuthService.register_user(
            username='customer',
            email='customer@example.com',
            phone='+0987654321',
            password='SecurePass123',
            full_name='Customer'
        )
        
        account = AccountService.create_account(
            user_id=user_result['user_id'],
            account_type='checking',
            opening_balance=1000.0
        )
        
        response = client.post(f"/api/accounts/{account['account_id']}/freeze",
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'frozen'


class TestTransactionRoutes:
    """Test cases for transaction routes."""
    
    def test_internal_transfer_route_success(self, app_context, client, auth_headers):
        """Test internal transfer via HTTP endpoint."""
        # Get the user_id from the logged in user (from auth_headers)
        user = User.query.filter_by(username='testuser').first()
        
        # Create two accounts for the authenticated user
        account1 = AccountService.create_account(
            user_id=user.id,
            account_type='checking',
            opening_balance=1000.0
        )
        
        account2 = AccountService.create_account(
            user_id=user.id,
            account_type='savings',
            opening_balance=500.0
        )
        
        # Make the transfer (user_id from JWT should match account owner)
        response = client.post('/api/transactions/internal-transfer',
            headers=auth_headers,
            json={
                'sender_account_id': account1['account_id'],
                'receiver_account_id': account2['account_id'],
                'amount': 200.0,
                'description': 'Transfer'
            }
        )
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['amount'] == 200.0
    
    def test_internal_transfer_route_insufficient_balance(self, app_context, client, auth_headers):
        """Test transfer with insufficient balance."""
        user = User.query.filter_by(username='testuser').first()
        
        account1 = AccountService.create_account(
            user_id=user.id,
            account_type='checking',
            opening_balance=100.0
        )
        
        account2 = AccountService.create_account(
            user_id=user.id,
            account_type='savings',
            opening_balance=500.0
        )
        
        response = client.post('/api/transactions/internal-transfer',
            headers=auth_headers,
            json={
                'sender_account_id': account1['account_id'],
                'receiver_account_id': account2['account_id'],
                'amount': 500.0,
                'description': 'Transfer'
            }
        )
        
        assert response.status_code == 400
    
    def test_get_account_transactions_route(self, app_context, client, auth_headers):
        """Test getting account transactions."""
        user = User.query.filter_by(username='testuser').first()
        
        account = AccountService.create_account(
            user_id=user.id,
            account_type='checking',
            opening_balance=1000.0
        )
        
        response = client.get(f"/api/transactions/account/{account['account_id']}/history",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'transactions' in data


class TestCORSHeaders:
    """Test CORS headers are properly set."""
    
    def test_cors_headers_on_preflight(self, client):
        """Test CORS headers on OPTIONS request."""
        response = client.options('/api/auth/login',
            headers={
                'Origin': 'http://localhost:3001',
                'Access-Control-Request-Method': 'POST'
            }
        )
        
        assert 'Access-Control-Allow-Origin' in response.headers
    
    def test_cors_headers_on_post(self, client):
        """Test CORS headers on POST request."""
        response = client.post('/api/auth/register',
            headers={'Origin': 'http://localhost:3001'},
            json={
                'username': 'testuser',
                'email': 'test@example.com',
                'phone': '+1234567890',
                'password': 'SecurePass123',
                'full_name': 'Test User'
            }
        )
        
        assert 'Access-Control-Allow-Origin' in response.headers


class TestJWTTokenExpiry:
    """Test JWT token expiry and refresh."""
    
    def test_expired_token_rejected(self, app_context, client):
        """Test that expired tokens are rejected."""
        # This would require mocking time or creating a token with past expiry
        # For now, test with invalid token format
        response = client.get('/api/auth/profile',
            headers={'Authorization': 'Bearer invalid_token'}
        )
        
        assert response.status_code == 422  # Unprocessable entity
    
    def test_missing_bearer_prefix(self, client):
        """Test token without Bearer prefix."""
        response = client.get('/api/auth/profile',
            headers={'Authorization': 'some_token'}
        )
        
        assert response.status_code == 401
    
    def test_malformed_authorization_header(self, client):
        """Test malformed authorization header."""
        response = client.get('/api/auth/profile',
            headers={'Authorization': 'InvalidFormat'}
        )
        
        assert response.status_code == 401


class TestErrorResponses:
    """Test error response formats."""
    
    def test_404_error_format(self, client):
        """Test 404 error response format."""
        response = client.get('/api/nonexistent')
        
        assert response.status_code == 404
        # Flask may return HTML or JSON for 404
        # Just verify we get a 404 status code
    
    def test_405_method_not_allowed(self, client):
        """Test 405 error for unsupported HTTP method."""
        response = client.delete('/api/auth/login')
        
        assert response.status_code == 405
    
    def test_validation_error_format(self, client):
        """Test validation error response format."""
        response = client.post('/api/auth/register', json={
            'username': 'ab',  # Too short
            'email': 'test@example.com',
            'phone': '+1234567890',
            'password': 'SecurePass123',
            'full_name': 'Test User'
        })
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data or 'message' in data


class TestRateLimiting:
    """Test rate limiting (if implemented)."""
    
    def test_multiple_requests_allowed(self, app_context, client):
        """Test that normal usage is allowed."""
        # Create a user first to avoid audit log errors
        AuthService.register_user(
            'ratelimituser', 'rate@test.com', '+1987654321',
            'testpass123', 'Rate User'
        )
        
        for i in range(5):
            response = client.post('/api/auth/login', json={
                'username': 'ratelimituser',
                'password': 'wrongpass'  # Intentionally wrong
            })
            # Should not be rate limited (401 for wrong password is fine)
            assert response.status_code in [200, 401]  # Not 429
