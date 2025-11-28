from datetime import datetime
from app.models import (
    Transaction, Account, User, AccountStatus, TransactionType, AuditAction, db
)
from app.security import log_audit

class TransactionService:
    """Service for handling financial transactions."""
    
    @staticmethod
    def internal_transfer(sender_user_id: int, sender_account_id: int, 
                         receiver_account_id: int, amount: float, 
                         description: str = None) -> dict:
        """
        Transfer money between accounts of the same user.
        
        Args:
            sender_user_id: ID of the user performing the transfer
            sender_account_id: ID of the sender's account
            receiver_account_id: ID of the receiver's account
            amount: Amount to transfer
            description: Optional description of the transfer
            
        Returns:
            Dictionary with transaction data
            
        Raises:
            ValueError: If validation fails
        """
        # Validate amount
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")
        
        # Get accounts
        sender_account = Account.query.get(sender_account_id)
        receiver_account = Account.query.get(receiver_account_id)
        
        if not sender_account or not receiver_account:
            raise ValueError("One or both accounts not found")
        
        # Verify both accounts belong to the same user
        if sender_account.user_id != sender_user_id or receiver_account.user_id != sender_user_id:
            log_audit(
                user_id=sender_user_id,
                action=AuditAction.SUSPICIOUS_ACTIVITY,
                resource_type='transaction',
                details='Attempted internal transfer with invalid account ownership'
            )
            raise ValueError("Invalid account ownership")
        
        # Check account status
        if sender_account.status != AccountStatus.ACTIVE:
            raise ValueError("Sender account is not active")
        
        if receiver_account.status != AccountStatus.ACTIVE:
            raise ValueError("Receiver account is not active")
        
        # Check balance
        if sender_account.balance < amount:
            log_audit(
                user_id=sender_user_id,
                action=AuditAction.SUSPICIOUS_ACTIVITY,
                resource_type='transaction',
                details=f'Insufficient balance for transfer: {amount}'
            )
            raise ValueError("Insufficient balance")
        
        try:
            # Perform transfer
            sender_account.balance -= amount
            receiver_account.balance += amount
            
            # Create DEBIT transaction record for sender
            debit_transaction = Transaction(
                sender_id=sender_user_id,
                sender_account_id=sender_account_id,
                receiver_account_id=receiver_account_id,
                amount=amount,
                transaction_type=TransactionType.DEBIT,
                description=description or 'Internal transfer'
            )
            
            # Create CREDIT transaction record for receiver
            credit_transaction = Transaction(
                sender_id=sender_user_id,
                sender_account_id=sender_account_id,
                receiver_account_id=receiver_account_id,
                amount=amount,
                transaction_type=TransactionType.CREDIT,
                description=description or 'Internal transfer'
            )
            
            db.session.add(debit_transaction)
            db.session.add(credit_transaction)
            sender_account.updated_at = datetime.utcnow()
            receiver_account.updated_at = datetime.utcnow()
            db.session.commit()
            
            log_audit(
                user_id=sender_user_id,
                action=AuditAction.TRANSFER,
                resource_type='transaction',
                resource_id=debit_transaction.transaction_id,
                details=f'Internal transfer: {amount} from {sender_account.account_number} to {receiver_account.account_number}'
            )
            
            return {
                'success': True,
                'transaction_id': debit_transaction.transaction_id,
                'sender_account': sender_account.account_number,
                'receiver_account': receiver_account.account_number,
                'amount': amount,
                'created_at': debit_transaction.created_at.isoformat()
            }
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Transfer failed: {str(e)}")
    
    @staticmethod
    def external_transfer(sender_user_id: int, sender_account_id: int, 
                         receiver_account_number: str, amount: float, 
                         description: str = None) -> dict:
        """
        Transfer money to another user's account.
        
        Args:
            sender_user_id: ID of the user performing the transfer
            sender_account_id: ID of the sender's account
            receiver_account_number: Account number of the receiver
            amount: Amount to transfer
            description: Optional description of the transfer
            
        Returns:
            Dictionary with transaction data
            
        Raises:
            ValueError: If validation fails
        """
        # Validate amount
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")
        
        # Get sender account
        sender_account = Account.query.get(sender_account_id)
        
        if not sender_account:
            raise ValueError("Sender account not found")
        
        # Verify account ownership
        if sender_account.user_id != sender_user_id:
            log_audit(
                user_id=sender_user_id,
                action=AuditAction.SUSPICIOUS_ACTIVITY,
                resource_type='transaction',
                details='Attempted external transfer with invalid account ownership'
            )
            raise ValueError("Invalid account ownership")
        
        # Check sender account status
        if sender_account.status != AccountStatus.ACTIVE:
            raise ValueError("Sender account is not active")
        
        # Get receiver account
        receiver_account = Account.query.filter_by(account_number=receiver_account_number).first()
        
        if not receiver_account:
            log_audit(
                user_id=sender_user_id,
                action=AuditAction.SUSPICIOUS_ACTIVITY,
                resource_type='transaction',
                details=f'Transfer to non-existent account: {receiver_account_number}'
            )
            raise ValueError("Receiver account not found")
        
        # Check receiver account status
        if receiver_account.status != AccountStatus.ACTIVE:
            raise ValueError("Receiver account is not active")
        
        # Check balance
        if sender_account.balance < amount:
            log_audit(
                user_id=sender_user_id,
                action=AuditAction.SUSPICIOUS_ACTIVITY,
                resource_type='transaction',
                details=f'Insufficient balance for external transfer: {amount}'
            )
            raise ValueError("Insufficient balance")
        
        try:
            # Perform transfer
            sender_account.balance -= amount
            receiver_account.balance += amount
            
            # Create DEBIT transaction record for sender
            debit_transaction = Transaction(
                sender_id=sender_user_id,
                sender_account_id=sender_account_id,
                receiver_account_id=receiver_account.id,
                amount=amount,
                transaction_type=TransactionType.DEBIT,
                description=description or 'External transfer'
            )
            
            # Create CREDIT transaction record for receiver
            credit_transaction = Transaction(
                sender_id=sender_user_id,
                sender_account_id=sender_account_id,
                receiver_account_id=receiver_account.id,
                amount=amount,
                transaction_type=TransactionType.CREDIT,
                description=description or 'External transfer'
            )
            
            db.session.add(debit_transaction)
            db.session.add(credit_transaction)
            sender_account.updated_at = datetime.utcnow()
            receiver_account.updated_at = datetime.utcnow()
            db.session.commit()
            
            log_audit(
                user_id=sender_user_id,
                action=AuditAction.TRANSFER,
                resource_type='transaction',
                resource_id=debit_transaction.transaction_id,
                details=f'External transfer: {amount} from {sender_account.account_number} to {receiver_account.account_number}'
            )
            
            return {
                'success': True,
                'transaction_id': debit_transaction.transaction_id,
                'sender_account': sender_account.account_number,
                'receiver_account': receiver_account.account_number,
                'amount': amount,
                'created_at': debit_transaction.created_at.isoformat()
            }
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Transfer failed: {str(e)}")
    
    @staticmethod
    def get_transaction(transaction_id: str) -> dict:
        """
        Get transaction details.
        
        Args:
            transaction_id: ID of the transaction
            
        Returns:
            Dictionary with transaction data
            
        Raises:
            ValueError: If transaction not found
        """
        transaction = Transaction.query.filter_by(transaction_id=transaction_id).first()
        
        if not transaction:
            raise ValueError("Transaction not found")
        
        return {
            'transaction_id': transaction.transaction_id,
            'sender_account': transaction.sender_account.account_number,
            'receiver_account': transaction.receiver_account.account_number,
            'amount': transaction.amount,
            'transaction_type': transaction.transaction_type.value,
            'description': transaction.description,
            'created_at': transaction.created_at.isoformat()
        }
    
    @staticmethod
    def get_account_transactions(account_id: int, limit: int = 5, offset: int = 0) -> dict:
        """
        Get recent transactions for an account.
        
        Args:
            account_id: ID of the account
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip
            
        Returns:
            Dictionary with transaction list and count
            
        Raises:
            ValueError: If account not found
        """
        account = Account.query.get(account_id)
        
        if not account:
            raise ValueError("Account not found")
        
        # Get transactions where account is sender or receiver
        # For each transaction, only show it once from the perspective of the viewing account
        transactions = Transaction.query.filter(
            ((Transaction.sender_account_id == account_id) & (Transaction.transaction_type == TransactionType.DEBIT)) |
            ((Transaction.receiver_account_id == account_id) & (Transaction.transaction_type == TransactionType.CREDIT))
        ).order_by(Transaction.created_at.desc()).limit(limit).offset(offset).all()
        
        total_count = Transaction.query.filter(
            ((Transaction.sender_account_id == account_id) & (Transaction.transaction_type == TransactionType.DEBIT)) |
            ((Transaction.receiver_account_id == account_id) & (Transaction.transaction_type == TransactionType.CREDIT))
        ).count()
        
        return {
            'account_id': account_id,
            'transactions': [
                {
                    'transaction_id': t.transaction_id,
                    'sender_account': t.sender_account.account_number,
                    'receiver_account': t.receiver_account.account_number,
                    'amount': t.amount,
                    'transaction_type': t.transaction_type.value,
                    'description': t.description,
                    'created_at': t.created_at.isoformat()
                }
                for t in transactions
            ],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }
    
    @staticmethod
    def filter_transactions(account_id: int, start_date: datetime = None, 
                           end_date: datetime = None, transaction_type: str = None,
                           min_amount: float = None, max_amount: float = None,
                           limit: int = 10, offset: int = 0) -> dict:
        """
        Filter transactions with various criteria.
        
        Args:
            account_id: ID of the account
            start_date: Start date for filtering
            end_date: End date for filtering
            transaction_type: Type of transaction (credit/debit)
            min_amount: Minimum transaction amount
            max_amount: Maximum transaction amount
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip
            
        Returns:
            Dictionary with filtered transactions
            
        Raises:
            ValueError: If account not found
        """
        account = Account.query.get(account_id)
        
        if not account:
            raise ValueError("Account not found")
        
        query = Transaction.query.filter(
            ((Transaction.sender_account_id == account_id) & (Transaction.transaction_type == TransactionType.DEBIT)) |
            ((Transaction.receiver_account_id == account_id) & (Transaction.transaction_type == TransactionType.CREDIT))
        )
        
        # Apply filters
        if start_date:
            query = query.filter(Transaction.created_at >= start_date)
        
        if end_date:
            query = query.filter(Transaction.created_at <= end_date)
        
        if transaction_type:
            try:
                trans_type = TransactionType[transaction_type.upper()]
                query = query.filter(Transaction.transaction_type == trans_type)
            except KeyError:
                raise ValueError(f"Invalid transaction type: {transaction_type}")
        
        if min_amount is not None:
            query = query.filter(Transaction.amount >= min_amount)
        
        if max_amount is not None:
            query = query.filter(Transaction.amount <= max_amount)
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        transactions = query.order_by(Transaction.created_at.desc()).limit(limit).offset(offset).all()
        
        return {
            'account_id': account_id,
            'transactions': [
                {
                    'transaction_id': t.transaction_id,
                    'sender_account': t.sender_account.account_number,
                    'receiver_account': t.receiver_account.account_number,
                    'amount': t.amount,
                    'transaction_type': t.transaction_type.value,
                    'description': t.description,
                    'created_at': t.created_at.isoformat()
                }
                for t in transactions
            ],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }

    @staticmethod
    def get_all_transactions(limit: int = 50, offset: int = 0) -> dict:
        """
        Return all transactions across all accounts for privileged roles.

        Args:
            limit: Max number of transactions
            offset: Number to skip

        Returns:
            Dictionary with transactions and pagination meta
        """
        query = Transaction.query
        total_count = query.count()
        transactions = query.order_by(Transaction.created_at.desc()).limit(limit).offset(offset).all()
        return {
            'transactions': [
                {
                    'transaction_id': t.transaction_id,
                    'sender_account': t.sender_account.account_number,
                    'receiver_account': t.receiver_account.account_number,
                    'amount': t.amount,
                    'transaction_type': t.transaction_type.value,
                    'description': t.description,
                    'created_at': t.created_at.isoformat()
                }
                for t in transactions
            ],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }
