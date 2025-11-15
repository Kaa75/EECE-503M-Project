import pytest
from datetime import datetime, timedelta
from app import create_app
from app.models import db, User, Account, Transaction, AccountStatus
from app.auth_service import AuthService
from app.account_service import AccountService
from app.transaction_service import TransactionService

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

@pytest.fixture
def test_user2(app_context):
    """Create a second test user."""
    result = AuthService.register_user(
        username='testuser2',
        email='test2@example.com',
        phone='+0987654321',
        password='SecurePass123',
        full_name='Test User 2'
    )
    return User.query.get(result['user_id'])

@pytest.fixture
def test_accounts(app_context, test_user):
    """Create test accounts."""
    account1 = AccountService.create_account(
        user_id=test_user.id,
        account_type='checking',
        opening_balance=1000.0
    )
    
    account2 = AccountService.create_account(
        user_id=test_user.id,
        account_type='savings',
        opening_balance=5000.0
    )
    
    return {
        'account1_id': account1['account_id'],
        'account2_id': account2['account_id']
    }

class TestTransactionService:
    """Test cases for TransactionService."""
    
    def test_internal_transfer_success(self, app_context, test_user, test_accounts):
        """Test successful internal transfer."""
        result = TransactionService.internal_transfer(
            sender_user_id=test_user.id,
            sender_account_id=test_accounts['account1_id'],
            receiver_account_id=test_accounts['account2_id'],
            amount=500.0,
            description='Test transfer'
        )
        
        assert result['success'] is True
        assert result['amount'] == 500.0
        
        # Verify balances
        account1 = Account.query.get(test_accounts['account1_id'])
        account2 = Account.query.get(test_accounts['account2_id'])
        
        assert account1.balance == 500.0
        assert account2.balance == 5500.0
    
    def test_internal_transfer_insufficient_balance(self, app_context, test_user, test_accounts):
        """Test internal transfer with insufficient balance."""
        with pytest.raises(ValueError, match='Insufficient balance'):
            TransactionService.internal_transfer(
                sender_user_id=test_user.id,
                sender_account_id=test_accounts['account1_id'],
                receiver_account_id=test_accounts['account2_id'],
                amount=2000.0
            )
    
    def test_internal_transfer_negative_amount(self, app_context, test_user, test_accounts):
        """Test internal transfer with negative amount."""
        with pytest.raises(ValueError, match='Transfer amount must be positive'):
            TransactionService.internal_transfer(
                sender_user_id=test_user.id,
                sender_account_id=test_accounts['account1_id'],
                receiver_account_id=test_accounts['account2_id'],
                amount=-100.0
            )
    
    def test_internal_transfer_zero_amount(self, app_context, test_user, test_accounts):
        """Test internal transfer with zero amount."""
        with pytest.raises(ValueError, match='Transfer amount must be positive'):
            TransactionService.internal_transfer(
                sender_user_id=test_user.id,
                sender_account_id=test_accounts['account1_id'],
                receiver_account_id=test_accounts['account2_id'],
                amount=0.0
            )
    
    def test_internal_transfer_frozen_sender_account(self, app_context, test_user, test_accounts):
        """Test internal transfer from frozen account."""
        AccountService.freeze_account(test_accounts['account1_id'], test_user.id)
        
        with pytest.raises(ValueError, match='Sender account is not active'):
            TransactionService.internal_transfer(
                sender_user_id=test_user.id,
                sender_account_id=test_accounts['account1_id'],
                receiver_account_id=test_accounts['account2_id'],
                amount=100.0
            )
    
    def test_internal_transfer_frozen_receiver_account(self, app_context, test_user, test_accounts):
        """Test internal transfer to frozen account."""
        AccountService.freeze_account(test_accounts['account2_id'], test_user.id)
        
        with pytest.raises(ValueError, match='Receiver account is not active'):
            TransactionService.internal_transfer(
                sender_user_id=test_user.id,
                sender_account_id=test_accounts['account1_id'],
                receiver_account_id=test_accounts['account2_id'],
                amount=100.0
            )
    
    def test_external_transfer_success(self, app_context, test_user, test_user2, test_accounts):
        """Test successful external transfer."""
        # Create account for second user
        account2_user2 = AccountService.create_account(
            user_id=test_user2.id,
            account_type='checking',
            opening_balance=0.0
        )
        
        account2_obj = Account.query.get(account2_user2['account_id'])
        
        result = TransactionService.external_transfer(
            sender_user_id=test_user.id,
            sender_account_id=test_accounts['account1_id'],
            receiver_account_number=account2_obj.account_number,
            amount=300.0,
            description='External transfer'
        )
        
        assert result['success'] is True
        assert result['amount'] == 300.0
        
        # Verify balances
        account1 = Account.query.get(test_accounts['account1_id'])
        assert account1.balance == 700.0
        assert account2_obj.balance == 300.0
    
    def test_external_transfer_invalid_receiver(self, app_context, test_user, test_accounts):
        """Test external transfer to non-existent account."""
        with pytest.raises(ValueError, match='Receiver account not found'):
            TransactionService.external_transfer(
                sender_user_id=test_user.id,
                sender_account_id=test_accounts['account1_id'],
                receiver_account_number='ACC-INVALID',
                amount=100.0
            )
    
    def test_external_transfer_insufficient_balance(self, app_context, test_user, test_user2, test_accounts):
        """Test external transfer with insufficient balance."""
        account2_user2 = AccountService.create_account(
            user_id=test_user2.id,
            account_type='checking',
            opening_balance=0.0
        )
        
        account2_obj = Account.query.get(account2_user2['account_id'])
        
        with pytest.raises(ValueError, match='Insufficient balance'):
            TransactionService.external_transfer(
                sender_user_id=test_user.id,
                sender_account_id=test_accounts['account1_id'],
                receiver_account_number=account2_obj.account_number,
                amount=2000.0
            )
    
    def test_get_transaction_success(self, app_context, test_user, test_accounts):
        """Test getting transaction details."""
        transfer_result = TransactionService.internal_transfer(
            sender_user_id=test_user.id,
            sender_account_id=test_accounts['account1_id'],
            receiver_account_id=test_accounts['account2_id'],
            amount=200.0
        )
        
        result = TransactionService.get_transaction(transfer_result['transaction_id'])
        
        assert result['amount'] == 200.0
        assert result['transaction_type'] == 'debit'
    
    def test_get_transaction_not_found(self, app_context):
        """Test getting non-existent transaction."""
        with pytest.raises(ValueError, match='Transaction not found'):
            TransactionService.get_transaction('invalid-id')
    
    def test_get_account_transactions(self, app_context, test_user, test_accounts):
        """Test getting account transaction history."""
        # Create multiple transactions
        for i in range(3):
            TransactionService.internal_transfer(
                sender_user_id=test_user.id,
                sender_account_id=test_accounts['account1_id'],
                receiver_account_id=test_accounts['account2_id'],
                amount=100.0
            )
        
        result = TransactionService.get_account_transactions(
            test_accounts['account1_id'],
            limit=5
        )
        
        assert result['total_count'] == 3
        assert len(result['transactions']) == 3
    
    def test_filter_transactions_by_date(self, app_context, test_user, test_accounts):
        """Test filtering transactions by date range."""
        # Create a transaction
        TransactionService.internal_transfer(
            sender_user_id=test_user.id,
            sender_account_id=test_accounts['account1_id'],
            receiver_account_id=test_accounts['account2_id'],
            amount=100.0
        )
        
        # Filter with date range
        start_date = datetime.utcnow() - timedelta(hours=1)
        end_date = datetime.utcnow() + timedelta(hours=1)
        
        result = TransactionService.filter_transactions(
            account_id=test_accounts['account1_id'],
            start_date=start_date,
            end_date=end_date
        )
        
        assert result['total_count'] == 1
    
    def test_filter_transactions_by_amount(self, app_context, test_user, test_accounts):
        """Test filtering transactions by amount range."""
        # Create transactions with different amounts
        TransactionService.internal_transfer(
            sender_user_id=test_user.id,
            sender_account_id=test_accounts['account1_id'],
            receiver_account_id=test_accounts['account2_id'],
            amount=100.0
        )
        
        TransactionService.internal_transfer(
            sender_user_id=test_user.id,
            sender_account_id=test_accounts['account1_id'],
            receiver_account_id=test_accounts['account2_id'],
            amount=500.0
        )
        
        # Filter by amount range
        result = TransactionService.filter_transactions(
            account_id=test_accounts['account1_id'],
            min_amount=200.0,
            max_amount=600.0
        )
        
        assert result['total_count'] == 1
        assert result['transactions'][0]['amount'] == 500.0
    
    def test_filter_transactions_by_type(self, app_context, test_user, test_accounts):
        """Test filtering transactions by type."""
        TransactionService.internal_transfer(
            sender_user_id=test_user.id,
            sender_account_id=test_accounts['account1_id'],
            receiver_account_id=test_accounts['account2_id'],
            amount=100.0
        )
        
        result = TransactionService.filter_transactions(
            account_id=test_accounts['account1_id'],
            transaction_type='debit'
        )
        
        assert result['total_count'] == 1
        assert result['transactions'][0]['transaction_type'] == 'debit'
