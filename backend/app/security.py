import bcrypt
import random
import string
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models import User, UserRole, AuditLog, AuditAction, db

def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    if not password or len(password) < 8:
        raise ValueError("Password must be at least 8 characters long")
    
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        password: Plain text password to verify
        password_hash: Hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception:
        return False

def generate_account_number() -> str:
    """
    Generate a unique account number.
    
    Returns:
        Account number string (format: ACC-XXXXXXXXXX)
    """
    random_part = ''.join(random.choices(string.digits, k=10))
    return f"ACC-{random_part}"

def sanitize_input(data: str, max_length: int = 255) -> str:
    """
    Sanitize user input to prevent injection attacks.
    
    Args:
        data: Input string to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not isinstance(data, str):
        raise ValueError("Input must be a string")
    
    # Remove potentially dangerous characters and patterns
    dangerous_chars = ['<', '>', '"', "'", ';', '--', '/*', '*/', 'xp_', 'sp_']
    sql_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'EXEC', 'EXECUTE']
    
    sanitized = data
    
    # Remove dangerous characters
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    # Remove SQL keywords (case-insensitive)
    for keyword in sql_keywords:
        sanitized = sanitized.replace(keyword, '')
        sanitized = sanitized.replace(keyword.lower(), '')
        sanitized = sanitized.replace(keyword.capitalize(), '')
    
    # Trim to max length
    return sanitized[:max_length].strip()

def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid email format, False otherwise
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if valid phone format, False otherwise
    """
    import re
    # Accept phone numbers with 7-20 digits, no spaces allowed
    pattern = r'^\+?[\d\-()]{7,20}$'
    return re.match(pattern, phone) is not None

def log_audit(user_id: int = None, action: AuditAction = None, 
              resource_type: str = None, resource_id: str = None, 
              details: str = None, ip_address: str = None) -> None:
    """
    Log an audit event.
    
    Args:
        user_id: ID of the user performing the action
        action: Type of action (AuditAction enum)
        resource_type: Type of resource affected
        resource_id: ID of the resource affected
        details: Additional details about the action
        ip_address: IP address of the request
    """
    try:
        # Try to get IP address from request if available
        if ip_address is None:
            try:
                from flask import request as flask_request
                if flask_request:
                    ip_address = flask_request.remote_addr
            except (RuntimeError, AttributeError):
                # Not in request context or request not available
                ip_address = None
        
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address
        )
        db.session.add(audit_log)
        db.session.commit()
    except Exception as e:
        print(f"Error logging audit: {str(e)}")

def check_account_lockout(user: User) -> bool:
    """
    Check if user account is locked due to failed login attempts.
    
    Args:
        user: User object to check
        
    Returns:
        True if account is locked, False otherwise
    """
    if user.locked_until and user.locked_until > datetime.utcnow():
        return True
    return False

def lock_account(user: User, duration_minutes: int = 15) -> None:
    """
    Lock a user account for a specified duration.
    
    Args:
        user: User object to lock
        duration_minutes: Duration of the lock in minutes
    """
    user.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
    user.failed_login_attempts = 0
    db.session.commit()

def unlock_account(user: User) -> None:
    """
    Unlock a user account.
    
    Args:
        user: User object to unlock
    """
    user.locked_until = None
    user.failed_login_attempts = 0
    db.session.commit()

def require_role(*allowed_roles):
    """
    Decorator to require specific roles for a route.
    
    Args:
        *allowed_roles: Variable number of UserRole values
        
    Returns:
        Decorated function
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user or user.role not in allowed_roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def require_auth(fn):
    """
    Decorator to require authentication.
    
    Args:
        fn: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        return fn(*args, **kwargs)
    return wrapper
