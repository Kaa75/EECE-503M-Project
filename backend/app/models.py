from datetime import datetime
from enum import Enum
import uuid
from app import db

class UserRole(Enum):
    """User roles in the system."""
    CUSTOMER = "customer"
    SUPPORT_AGENT = "support_agent"
    AUDITOR = "auditor"
    ADMIN = "admin"

class AccountStatus(Enum):
    """Account status values."""
    ACTIVE = "active"
    FROZEN = "frozen"
    CLOSED = "closed"

class AccountType(Enum):
    """Account types."""
    CHECKING = "checking"
    SAVINGS = "savings"

class TransactionType(Enum):
    """Transaction types."""
    CREDIT = "credit"
    DEBIT = "debit"

class TicketStatus(Enum):
    """Support ticket status values."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"

class AuditAction(Enum):
    """Audit log action types."""
    LOGIN = "login"
    LOGIN_FAILED = "login_failed"
    ACCOUNT_FREEZE = "account_freeze"
    ACCOUNT_UNFREEZE = "account_unfreeze"
    TRANSFER = "transfer"
    ADMIN_ACTION = "admin_action"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"

class User(db.Model):
    """User model for authentication and profile management."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role = db.Column(db.Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    must_change_credentials = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    accounts = db.relationship('Account', backref='owner', lazy=True, foreign_keys='Account.user_id')
    sent_transactions = db.relationship('Transaction', backref='sender', lazy=True, foreign_keys='Transaction.sender_id')
    tickets = db.relationship('SupportTicket', backref='customer', lazy=True, foreign_keys='SupportTicket.customer_id')
    ticket_responses = db.relationship('SupportTicket', backref='assigned_agent', lazy=True, foreign_keys='SupportTicket.assigned_agent_id')
    audit_logs = db.relationship('AuditLog', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Account(db.Model):
    """Account model for user bank accounts."""
    __tablename__ = 'accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    account_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    account_type = db.Column(db.Enum(AccountType), nullable=False)
    balance = db.Column(db.Float, default=0.0, nullable=False)
    status = db.Column(db.Enum(AccountStatus), default=AccountStatus.ACTIVE, nullable=False)
    opening_balance = db.Column(db.Float, default=0.0, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    transactions_sent = db.relationship('Transaction', backref='sender_account', lazy=True, foreign_keys='Transaction.sender_account_id')
    transactions_received = db.relationship('Transaction', backref='receiver_account', lazy=True, foreign_keys='Transaction.receiver_account_id')
    
    def __repr__(self):
        return f'<Account {self.account_number}>'

class Transaction(db.Model):
    """Transaction model for tracking transfers and payments."""
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sender_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    receiver_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    transaction_type = db.Column(db.Enum(TransactionType), nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<Transaction {self.transaction_id}>'

class SupportTicket(db.Model):
    """Support ticket model for customer support requests."""
    __tablename__ = 'support_tickets'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_agent_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    subject = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.Enum(TicketStatus), default=TicketStatus.OPEN, nullable=False)
    priority = db.Column(db.String(20), default='medium')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    notes = db.relationship('TicketNote', backref='ticket', lazy=True)
    
    def __repr__(self):
        return f'<SupportTicket {self.ticket_id}>'

class TicketNote(db.Model):
    """Ticket note model for support ticket communications."""
    __tablename__ = 'ticket_notes'
    
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('support_tickets.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_internal = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    author = db.relationship('User', backref='ticket_notes', lazy=True)
    
    def __repr__(self):
        return f'<TicketNote {self.id} for Ticket {self.ticket_id}>'


class AuditLog(db.Model):
    """Audit log model for tracking system activities."""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.Enum(AuditAction), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    resource_type = db.Column(db.String(50), nullable=True)
    resource_id = db.Column(db.String(100), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f'<AuditLog {self.action.value} by User {self.user_id}>'

