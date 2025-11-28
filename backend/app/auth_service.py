from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError
from flask_jwt_extended import create_access_token, create_refresh_token
from app.models import User, UserRole, AuditAction, db
from app.security import (
    hash_password, verify_password, sanitize_input, validate_email,
    validate_phone, log_audit, check_account_lockout, lock_account, unlock_account
)

class AuthService:
    """Service for handling user authentication and authorization."""
    # Defaults will be overridden by config values when accessed inside methods
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION = 15  # minutes
    
    @staticmethod
    def register_user(username: str, email: str, phone: str, password: str, 
                     full_name: str, role: UserRole = UserRole.CUSTOMER) -> dict:
        """
        Register a new user.
        
        Args:
            username: Unique username
            email: User email address
            phone: User phone number
            password: User password (will be hashed)
            full_name: User's full name
            role: User role (default: CUSTOMER)
            
        Returns:
            Dictionary with user data and success status
            
        Raises:
            ValueError: If validation fails
        """
        # Validate inputs
        if not username or len(username) < 3:
            raise ValueError("Username must be at least 3 characters")
        
        if len(username) > 50:
            raise ValueError("Username must not exceed 50 characters")
        
        if not email or not validate_email(email):
            raise ValueError("Invalid email format")
        
        if not phone or not validate_phone(phone):
            raise ValueError("Invalid phone format")
        
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters")
        
        if not full_name or len(full_name) < 2:
            raise ValueError("Full name must be at least 2 characters")
        
        # Check if user already exists (case-insensitive username)
        existing_user = User.query.filter(
            (db.func.lower(User.username) == username.lower()) | (User.email == email)
        ).first()
        
        if existing_user:
            raise ValueError("Username or email already exists")
        
        # Sanitize inputs
        username = sanitize_input(username, 80).lower()  # Store username in lowercase
        email = sanitize_input(email, 120)
        full_name = sanitize_input(full_name, 120)
        
        # Create new user
        try:
            user = User(
                username=username,
                email=email,
                phone=phone,
                password_hash=hash_password(password),
                full_name=full_name,
                role=role,
                is_active=True
            )
            
            db.session.add(user)
            db.session.commit()
            
            log_audit(
                user_id=user.id,
                action=AuditAction.ADMIN_ACTION,
                resource_type='user',
                resource_id=str(user.id),
                details=f'User registered: {username}'
            )
            
            return {
                'success': True,
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'role': user.role.value
            }
        except IntegrityError:
            db.session.rollback()
            raise ValueError("Username or email already exists")
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Failed to register user: {str(e)}")
    
    @staticmethod
    def login(username: str, password: str, ip_address: str = None) -> dict:
        """
        Authenticate a user and return JWT tokens.
        
        Args:
            username: User username (case-insensitive)
            password: User password
            ip_address: IP address of the login request
            
        Returns:
            Dictionary with JWT tokens and user data
            
        Raises:
            ValueError: If authentication fails
        """
        # Find user (case-insensitive username)
        user = User.query.filter(db.func.lower(User.username) == username.lower()).first()
        
        if not user:
            log_audit(
                action=AuditAction.LOGIN_FAILED,
                resource_type='user',
                resource_id=username,
                details='User not found',
                ip_address=ip_address
            )
            raise ValueError("Invalid username or password")
        
        # Check if account is locked
        # Use configured lockout duration if present
        from flask import current_app
        max_attempts = current_app.config.get('MAX_LOGIN_ATTEMPTS', AuthService.MAX_LOGIN_ATTEMPTS)
        lockout_minutes = current_app.config.get('LOCKOUT_DURATION', AuthService.LOCKOUT_DURATION)

        if check_account_lockout(user):
            log_audit(
                user_id=user.id,
                action=AuditAction.LOGIN_FAILED,
                resource_type='user',
                resource_id=str(user.id),
                details='Account locked due to failed login attempts',
                ip_address=ip_address
            )
            raise ValueError("Too many failed login attempts. Account is locked.")
        
        # Verify password
        if not verify_password(password, user.password_hash):
            user.failed_login_attempts += 1
            
            if user.failed_login_attempts >= max_attempts:
                lock_account(user, lockout_minutes)
                log_audit(
                    user_id=user.id,
                    action=AuditAction.LOGIN_FAILED,
                    resource_type='user',
                    resource_id=str(user.id),
                    details='Account locked after multiple failed attempts',
                    ip_address=ip_address
                )
                raise ValueError("Too many failed login attempts. Account locked.")
            
            db.session.commit()
            
            log_audit(
                user_id=user.id,
                action=AuditAction.LOGIN_FAILED,
                resource_type='user',
                resource_id=str(user.id),
                details=f'Failed login attempt {user.failed_login_attempts}',
                ip_address=ip_address
            )
            
            raise ValueError("Invalid username or password")
        
        # Check if user is active
        if not user.is_active:
            log_audit(
                user_id=user.id,
                action=AuditAction.LOGIN_FAILED,
                resource_type='user',
                resource_id=str(user.id),
                details='Inactive user attempted login',
                ip_address=ip_address
            )
            raise ValueError("User account is inactive")
        
        # Reset failed login attempts
        user.failed_login_attempts = 0
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Log successful login
        log_audit(
            user_id=user.id,
            action=AuditAction.LOGIN,
            resource_type='user',
            resource_id=str(user.id),
            details='Successful login',
            ip_address=ip_address
        )
        
        # Create tokens with string identity (tokens still issued so frontend can call change-credentials)
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))

        return {
            'success': True,
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role.value,
            'full_name': user.full_name,
            'must_change_credentials': user.must_change_credentials
        }
    
    @staticmethod
    def change_password(user_id: int, old_password: str, new_password: str) -> dict:
        """
        Change user password.
        
        Args:
            user_id: ID of the user
            old_password: Current password
            new_password: New password
            
        Returns:
            Dictionary with success status
            
        Raises:
            ValueError: If validation fails
        """
        user = User.query.get(user_id)
        
        if not user:
            raise ValueError("User not found")
        
        # Verify old password
        if not verify_password(old_password, user.password_hash):
            log_audit(
                user_id=user.id,
                action=AuditAction.ADMIN_ACTION,
                resource_type='user',
                resource_id=str(user.id),
                details='Failed password change attempt'
            )
            raise ValueError("Invalid current password")
        
        # Validate new password
        if not new_password or len(new_password) < 8:
            raise ValueError("New password must be at least 8 characters")
        
        if old_password == new_password:
            raise ValueError("New password must be different from current password")
        
        # Update password
        try:
            user.password_hash = hash_password(new_password)
            db.session.commit()
            
            log_audit(
                user_id=user.id,
                action=AuditAction.ADMIN_ACTION,
                resource_type='user',
                resource_id=str(user.id),
                details='Password changed'
            )
            
            return {'success': True, 'message': 'Password changed successfully'}
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Failed to change password: {str(e)}")

    @staticmethod
    def change_credentials(user_id: int, current_password: str, new_username: str, new_password: str) -> dict:
        """Change both username and password for a user (admin self-rotation).

        Args:
            user_id: ID of the user performing change
            current_password: Existing password for verification
            new_username: Desired new unique username
            new_password: New password meeting policy

        Returns:
            Dict with success status

        Raises:
            ValueError on validation failures
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")

        # Verify current password
        if not verify_password(current_password, user.password_hash):
            raise ValueError("Invalid current password")

        # Validate new username
        if not new_username or len(new_username) < 3 or len(new_username) > 50:
            raise ValueError("Username must be 3-50 characters")

        normalized_username = new_username.lower()
        existing = User.query.filter(db.func.lower(User.username) == normalized_username, User.id != user_id).first()
        if existing:
            raise ValueError("Username already taken")

        # Validate new password
        if not new_password or len(new_password) < 8:
            raise ValueError("New password must be at least 8 characters")
        if verify_password(new_password, user.password_hash):
            raise ValueError("New password must differ from current password")

        try:
            user.username = normalized_username
            user.password_hash = hash_password(new_password)
            user.must_change_credentials = False
            user.updated_at = datetime.utcnow()
            db.session.commit()

            log_audit(
                user_id=user.id,
                action=AuditAction.ADMIN_ACTION,
                resource_type='user',
                resource_id=str(user.id),
                details='Credentials rotated (username + password)'
            )

            return {'success': True, 'message': 'Credentials updated', 'username': user.username}
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Failed to update credentials: {str(e)}")
    
    @staticmethod
    def get_user(user_id: int) -> dict:
        """
        Get user information.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary with user data
            
        Raises:
            ValueError: If user not found
        """
        user = User.query.get(user_id)
        
        if not user:
            raise ValueError("User not found")
        
        return {
            'id': user.id,
            'user_id': user.id,  # Keep for backward compatibility
            'username': user.username,
            'email': user.email,
            'phone': user.phone,
            'full_name': user.full_name,
            'role': user.role.value,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat(),
            'last_login': user.last_login.isoformat() if user.last_login else None
        }
    
    @staticmethod
    def update_profile(user_id: int, email: str = None, phone: str = None, 
                      full_name: str = None) -> dict:
        """
        Update user profile information.
        
        Args:
            user_id: ID of the user
            email: New email (optional)
            phone: New phone (optional)
            full_name: New full name (optional)
            
        Returns:
            Dictionary with updated user data
            
        Raises:
            ValueError: If validation fails
        """
        user = User.query.get(user_id)
        
        if not user:
            raise ValueError("User not found")
        
        try:
            if email:
                if not validate_email(email):
                    raise ValueError("Invalid email format")
                
                existing = User.query.filter(
                    User.email == email,
                    User.id != user_id
                ).first()
                
                if existing:
                    raise ValueError("Email already in use")
                
                user.email = sanitize_input(email, 120)
            
            if phone:
                if not validate_phone(phone):
                    raise ValueError("Invalid phone format")
                user.phone = phone
            
            if full_name:
                if len(full_name) < 2:
                    raise ValueError("Full name must be at least 2 characters")
                user.full_name = sanitize_input(full_name, 120)
            
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            log_audit(
                user_id=user.id,
                action=AuditAction.ADMIN_ACTION,
                resource_type='user',
                resource_id=str(user.id),
                details='Profile updated'
            )
            
            return {
                'success': True,
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
                'phone': user.phone,
                'full_name': user.full_name,
                'role': user.role.value
            }
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Failed to update profile: {str(e)}")
