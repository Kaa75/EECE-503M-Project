from datetime import datetime
from app.models import (
    Account, User, AccountStatus, AccountType, AuditAction, db
)
from app.security import generate_account_number, log_audit

class AccountService:
    """Service for handling account management operations."""
    
    @staticmethod
    def create_account(user_id: int, account_type: str, opening_balance: float = 0.0) -> dict:
        """
        Create a new account for a user.
        
        Args:
            user_id: ID of the account owner
            account_type: Type of account (checking/savings)
            opening_balance: Initial account balance
            
        Returns:
            Dictionary with account data
            
        Raises:
            ValueError: If validation fails
        """
        # Validate user exists
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        # Check account limit (max 20 accounts per user)
        existing_accounts_count = Account.query.filter_by(user_id=user_id).count()
        if existing_accounts_count >= 20:
            raise ValueError("Account limit reached. Maximum 20 accounts per user.")
        
        # Validate account type
        try:
            acc_type = AccountType[account_type.upper()]
        except KeyError:
            raise ValueError(f"Invalid account type: {account_type}")
        
        # Validate opening balance
        if opening_balance < 0:
            raise ValueError("Opening balance cannot be negative")
        
        try:
            # Generate unique account number
            account_number = generate_account_number()
            
            # Ensure uniqueness
            while Account.query.filter_by(account_number=account_number).first():
                account_number = generate_account_number()
            
            # Create account
            account = Account(
                account_number=account_number,
                user_id=user_id,
                account_type=acc_type,
                balance=opening_balance,
                opening_balance=opening_balance,
                status=AccountStatus.ACTIVE
            )
            
            db.session.add(account)
            db.session.commit()
            
            log_audit(
                user_id=user_id,
                action=AuditAction.ADMIN_ACTION,
                resource_type='account',
                resource_id=str(account.id),
                details=f'Account created: {account_number}'
            )
            
            return {
                'success': True,
                'account_id': account.id,
                'account_number': account.account_number,
                'account_type': account.account_type.value,
                'balance': account.balance,
                'status': account.status.value,
                'created_at': account.created_at.isoformat()
            }
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Failed to create account: {str(e)}")
    
    @staticmethod
    def get_account(account_id: int) -> dict:
        """
        Get account information.
        
        Args:
            account_id: ID of the account
            
        Returns:
            Dictionary with account data
            
        Raises:
            ValueError: If account not found
        """
        account = Account.query.get(account_id)
        
        if not account:
            raise ValueError("Account not found")
        
        return {
            'account_id': account.id,
            'account_number': account.account_number,
            'user_id': account.user_id,
            'account_type': account.account_type.value,
            'balance': account.balance,
            'status': account.status.value,
            'opening_balance': account.opening_balance,
            'created_at': account.created_at.isoformat(),
            'updated_at': account.updated_at.isoformat()
        }
    
    @staticmethod
    def get_user_accounts(user_id: int) -> list:
        """
        Get all accounts for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of account dictionaries
        """
        accounts = Account.query.filter_by(user_id=user_id).all()
        
        return [
            {
                'id': account.id,
                'account_number': account.account_number,
                'user_id': account.user_id,
                'account_type': account.account_type.value,
                'balance': account.balance,
                'opening_balance': account.opening_balance,
                'status': account.status.value,
                'created_at': account.created_at.isoformat()
            }
            for account in accounts
        ]
    
    @staticmethod
    def freeze_account(account_id: int, admin_id: int) -> dict:
        """
        Freeze an account (admin only).
        
        Args:
            account_id: ID of the account to freeze
            admin_id: ID of the admin performing the action
            
        Returns:
            Dictionary with updated account data
            
        Raises:
            ValueError: If account not found or already frozen
        """
        account = Account.query.get(account_id)
        
        if not account:
            raise ValueError("Account not found")
        
        if account.status == AccountStatus.FROZEN:
            raise ValueError("Account is already frozen")
        
        try:
            account.status = AccountStatus.FROZEN
            account.updated_at = datetime.utcnow()
            db.session.commit()
            
            log_audit(
                user_id=admin_id,
                action=AuditAction.ACCOUNT_FREEZE,
                resource_type='account',
                resource_id=str(account.id),
                details=f'Account frozen: {account.account_number}'
            )
            
            return {
                'success': True,
                'account_id': account.id,
                'account_number': account.account_number,
                'status': account.status.value
            }
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Failed to freeze account: {str(e)}")
    
    @staticmethod
    def unfreeze_account(account_id: int, admin_id: int) -> dict:
        """
        Unfreeze an account (admin only).
        
        Args:
            account_id: ID of the account to unfreeze
            admin_id: ID of the admin performing the action
            
        Returns:
            Dictionary with updated account data
            
        Raises:
            ValueError: If account not found or not frozen
        """
        account = Account.query.get(account_id)
        
        if not account:
            raise ValueError("Account not found")
        
        if account.status != AccountStatus.FROZEN:
            raise ValueError("Account is not frozen")
        
        try:
            account.status = AccountStatus.ACTIVE
            account.updated_at = datetime.utcnow()
            db.session.commit()
            
            log_audit(
                user_id=admin_id,
                action=AuditAction.ACCOUNT_UNFREEZE,
                resource_type='account',
                resource_id=str(account.id),
                details=f'Account unfrozen: {account.account_number}'
            )
            
            return {
                'success': True,
                'account_id': account.id,
                'account_number': account.account_number,
                'status': account.status.value
            }
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Failed to unfreeze account: {str(e)}")
    
    @staticmethod
    def get_account_balance(account_id: int) -> dict:
        """
        Get current account balance.
        
        Args:
            account_id: ID of the account
            
        Returns:
            Dictionary with balance information
            
        Raises:
            ValueError: If account not found
        """
        account = Account.query.get(account_id)
        
        if not account:
            raise ValueError("Account not found")
        
        return {
            'account_id': account.id,
            'account_number': account.account_number,
            'balance': account.balance,
            'status': account.status.value
        }
    
    @staticmethod
    def close_account(account_id: int, admin_id: int) -> dict:
        """
        Close an account (admin only).
        
        Args:
            account_id: ID of the account to close
            admin_id: ID of the admin performing the action
            
        Returns:
            Dictionary with updated account data
            
        Raises:
            ValueError: If account not found or has balance
        """
        account = Account.query.get(account_id)
        
        if not account:
            raise ValueError("Account not found")
        
        if account.balance != 0:
            raise ValueError("Cannot close account with remaining balance")
        
        try:
            account.status = AccountStatus.CLOSED
            account.updated_at = datetime.utcnow()
            db.session.commit()
            
            log_audit(
                user_id=admin_id,
                action=AuditAction.ADMIN_ACTION,
                resource_type='account',
                resource_id=str(account.id),
                details=f'Account closed: {account.account_number}'
            )
            
            return {
                'success': True,
                'account_id': account.id,
                'account_number': account.account_number,
                'status': account.status.value
            }
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Failed to close account: {str(e)}")
