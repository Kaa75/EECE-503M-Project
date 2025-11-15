import pytest
from app import create_app
from app.models import db, User, Account, UserRole, AccountStatus, AccountType
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
def app_context(app):
    """Create application context."""
    with app.app_context():
        yield

@pytest.fixture
def test_user(app_context):
    """Create a test user."""
    result = AuthService.register_user(
        username='testuser',
        email='test@example.com',
        phone='+1234567890',
        password='SecurePass123',
        full_name='Test User'
    )
    return User.query.get(result['user_id'])

class TestAccountService:
    """Test cases for AccountService."""
    
    def test_create_account_success(self, app_context, test_user):
        """Test successful account creation."""
        result = AccountService.create_account(
            user_id=test_user.id,
            account_type='checking',
            opening_balance=1000.0
        )
        
        assert result['success'] is True
        assert result['account_type'] == 'checking'
        assert result['balance'] == 1000.0
        assert result['status'] == 'active'
        assert result['account_number'].startswith('ACC-')
    
    def test_create_account_savings(self, app_context, test_user):
        """Test creating a savings account."""
        result = AccountService.create_account(
            user_id=test_user.id,
            account_type='savings',
            opening_balance=5000.0
        )
        
        assert result['account_type'] == 'savings'
        assert result['balance'] == 5000.0
    
    def test_create_account_invalid_type(self, app_context, test_user):
        """Test account creation with invalid type."""
        with pytest.raises(ValueError, match='Invalid account type'):
            AccountService.create_account(
                user_id=test_user.id,
                account_type='invalid',
                opening_balance=1000.0
            )
    
    def test_create_account_negative_balance(self, app_context, test_user):
        """Test account creation with negative balance."""
        with pytest.raises(ValueError, match='Opening balance cannot be negative'):
            AccountService.create_account(
                user_id=test_user.id,
                account_type='checking',
                opening_balance=-100.0
            )
    
    def test_create_account_user_not_found(self, app_context):
        """Test account creation for non-existent user."""
        with pytest.raises(ValueError, match='User not found'):
            AccountService.create_account(
                user_id=999,
                account_type='checking',
                opening_balance=1000.0
            )
    
    def test_get_account_success(self, app_context, test_user):
        """Test getting account information."""
        account_result = AccountService.create_account(
            user_id=test_user.id,
            account_type='checking',
            opening_balance=1000.0
        )
        
        account = Account.query.get(account_result['account_id'])
        result = AccountService.get_account(account.id)
        
        assert result['account_number'] == account.account_number
        assert result['balance'] == 1000.0
        assert result['status'] == 'active'
    
    def test_get_account_not_found(self, app_context):
        """Test getting non-existent account."""
        with pytest.raises(ValueError, match='Account not found'):
            AccountService.get_account(999)
    
    def test_get_user_accounts(self, app_context, test_user):
        """Test getting all accounts for a user."""
        # Create multiple accounts
        AccountService.create_account(
            user_id=test_user.id,
            account_type='checking',
            opening_balance=1000.0
        )
        
        AccountService.create_account(
            user_id=test_user.id,
            account_type='savings',
            opening_balance=5000.0
        )
        
        result = AccountService.get_user_accounts(test_user.id)
        
        assert len(result) == 2
        assert result[0]['account_type'] in ['checking', 'savings']
        assert result[1]['account_type'] in ['checking', 'savings']
    
    def test_freeze_account_success(self, app_context, test_user):
        """Test successful account freeze."""
        account_result = AccountService.create_account(
            user_id=test_user.id,
            account_type='checking',
            opening_balance=1000.0
        )
        
        account = Account.query.get(account_result['account_id'])
        
        result = AccountService.freeze_account(account.id, test_user.id)
        
        assert result['success'] is True
        assert result['status'] == 'frozen'
        
        # Verify account is frozen in database
        account = Account.query.get(account.id)
        assert account.status == AccountStatus.FROZEN
    
    def test_freeze_account_already_frozen(self, app_context, test_user):
        """Test freezing an already frozen account."""
        account_result = AccountService.create_account(
            user_id=test_user.id,
            account_type='checking',
            opening_balance=1000.0
        )
        
        account = Account.query.get(account_result['account_id'])
        
        AccountService.freeze_account(account.id, test_user.id)
        
        with pytest.raises(ValueError, match='Account is already frozen'):
            AccountService.freeze_account(account.id, test_user.id)
    
    def test_unfreeze_account_success(self, app_context, test_user):
        """Test successful account unfreeze."""
        account_result = AccountService.create_account(
            user_id=test_user.id,
            account_type='checking',
            opening_balance=1000.0
        )
        
        account = Account.query.get(account_result['account_id'])
        
        AccountService.freeze_account(account.id, test_user.id)
        result = AccountService.unfreeze_account(account.id, test_user.id)
        
        assert result['success'] is True
        assert result['status'] == 'active'
        
        # Verify account is active in database
        account = Account.query.get(account.id)
        assert account.status == AccountStatus.ACTIVE
    
    def test_unfreeze_account_not_frozen(self, app_context, test_user):
        """Test unfreezing an account that is not frozen."""
        account_result = AccountService.create_account(
            user_id=test_user.id,
            account_type='checking',
            opening_balance=1000.0
        )
        
        account = Account.query.get(account_result['account_id'])
        
        with pytest.raises(ValueError, match='Account is not frozen'):
            AccountService.unfreeze_account(account.id, test_user.id)
    
    def test_get_account_balance(self, app_context, test_user):
        """Test getting account balance."""
        account_result = AccountService.create_account(
            user_id=test_user.id,
            account_type='checking',
            opening_balance=1500.0
        )
        
        account = Account.query.get(account_result['account_id'])
        result = AccountService.get_account_balance(account.id)
        
        assert result['balance'] == 1500.0
        assert result['status'] == 'active'
    
    def test_close_account_success(self, app_context, test_user):
        """Test successful account closure."""
        account_result = AccountService.create_account(
            user_id=test_user.id,
            account_type='checking',
            opening_balance=0.0
        )
        
        account = Account.query.get(account_result['account_id'])
        
        result = AccountService.close_account(account.id, test_user.id)
        
        assert result['success'] is True
        assert result['status'] == 'closed'
    
    def test_close_account_with_balance(self, app_context, test_user):
        """Test closing account with remaining balance."""
        account_result = AccountService.create_account(
            user_id=test_user.id,
            account_type='checking',
            opening_balance=1000.0
        )
        
        account = Account.query.get(account_result['account_id'])
        
        with pytest.raises(ValueError, match='Cannot close account with remaining balance'):
            AccountService.close_account(account.id, test_user.id)
    
    def test_account_number_uniqueness(self, app_context, test_user):
        """Test that account numbers are unique."""
        result1 = AccountService.create_account(
            user_id=test_user.id,
            account_type='checking',
            opening_balance=1000.0
        )
        
        result2 = AccountService.create_account(
            user_id=test_user.id,
            account_type='savings',
            opening_balance=5000.0
        )
        
        assert result1['account_number'] != result2['account_number']
