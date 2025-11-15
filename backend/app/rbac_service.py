from app.models import User, UserRole, AuditAction, db
from app.security import log_audit

class RBACService:
    """Service for managing Role-Based Access Control."""
    
    # Permission matrix
    PERMISSIONS = {
        UserRole.CUSTOMER: {
            'register_login': True,
            'manage_own_profile': True,
            'view_own_accounts': True,
            'view_all_user_accounts': False,
            'create_accounts': True,
            'internal_transfers': True,
            'external_transfers': True,
            'view_own_transactions': True,
            'view_all_transactions': False,
            'freeze_unfreeze_accounts': False,
            'assign_change_user_roles': False,
            'view_audit_security_logs': False,
            'manage_support_tickets': True,
            'view_open_tickets': False,
            'update_ticket_status': False,
            'add_ticket_notes': True,  # Customers can add notes to their own tickets
        },
        UserRole.SUPPORT_AGENT: {
            'register_login': True,
            'manage_own_profile': True,
            'view_own_accounts': True,
            'view_all_user_accounts': True,
            'create_accounts': False,
            'internal_transfers': False,
            'external_transfers': False,
            'view_own_transactions': True,
            'view_all_transactions': True,
            'freeze_unfreeze_accounts': False,
            'assign_change_user_roles': False,
            'view_audit_security_logs': False,
            'manage_support_tickets': True,
            'view_open_tickets': True,
            'update_ticket_status': True,
            'add_ticket_notes': True,
        },
        UserRole.AUDITOR: {
            'register_login': True,
            'manage_own_profile': False,
            'view_own_accounts': True,
            'view_all_user_accounts': True,
            'create_accounts': False,
            'internal_transfers': False,
            'external_transfers': False,
            'view_own_transactions': True,
            'view_all_transactions': True,
            'freeze_unfreeze_accounts': False,
            'assign_change_user_roles': False,
            'view_audit_security_logs': True,
            'manage_support_tickets': False,
            'view_open_tickets': False,
            'update_ticket_status': False,
            'add_ticket_notes': False,
        },
        UserRole.ADMIN: {
            'register_login': True,
            'manage_own_profile': True,
            'view_own_accounts': True,
            'view_all_user_accounts': True,
            'create_accounts': True,
            'internal_transfers': True,
            'external_transfers': True,
            'view_own_transactions': True,
            'view_all_transactions': True,
            'freeze_unfreeze_accounts': True,
            'assign_change_user_roles': True,
            'view_audit_security_logs': True,
            'manage_support_tickets': True,
            'view_open_tickets': True,
            'update_ticket_status': True,
            'add_ticket_notes': True,
        }
    }
    
    @staticmethod
    def has_permission(user: User, permission: str) -> bool:
        """
        Check if a user has a specific permission.
        
        Args:
            user: User object
            permission: Permission name to check
            
        Returns:
            True if user has permission, False otherwise
        """
        if not user:
            return False
        
        if user.role not in RBACService.PERMISSIONS:
            return False
        
        return RBACService.PERMISSIONS[user.role].get(permission, False)
    
    @staticmethod
    def check_permission(user_id: int, permission: str) -> bool:
        """
        Check if a user has a specific permission by user ID.
        
        Args:
            user_id: ID of the user
            permission: Permission name to check
            
        Returns:
            True if user has permission, False otherwise
        """
        user = User.query.get(user_id)
        return RBACService.has_permission(user, permission)
    
    @staticmethod
    def get_user_permissions(user_id: int) -> dict:
        """
        Get all permissions for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary with user role and permissions
            
        Raises:
            ValueError: If user not found
        """
        user = User.query.get(user_id)
        
        if not user:
            raise ValueError("User not found")
        
        return {
            'user_id': user_id,
            'username': user.username,
            'role': user.role.value,
            'permissions': RBACService.PERMISSIONS.get(user.role, {})
        }
    
    @staticmethod
    def assign_role(user_id: int, new_role: str, admin_id: int) -> dict:
        """
        Assign a new role to a user (admin only).
        
        Args:
            user_id: ID of the user to assign role to
            new_role: New role (customer/support_agent/auditor/admin)
            admin_id: ID of the admin performing the action
            
        Returns:
            Dictionary with updated user data
            
        Raises:
            ValueError: If validation fails
        """
        user = User.query.get(user_id)
        
        if not user:
            raise ValueError("User not found")
        
        # Validate role
        try:
            role = UserRole[new_role.upper()]
        except KeyError:
            raise ValueError(f"Invalid role: {new_role}")
        
        try:
            old_role = user.role.value
            user.role = role
            db.session.commit()
            
            log_audit(
                user_id=admin_id,
                action=AuditAction.ADMIN_ACTION,
                resource_type='user',
                resource_id=str(user_id),
                details=f'Role changed from {old_role} to {new_role}'
            )
            
            return {
                'success': True,
                'user_id': user.id,
                'username': user.username,
                'old_role': old_role,
                'new_role': user.role.value
            }
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Failed to assign role: {str(e)}")
    
    @staticmethod
    def get_users_by_role(role: str, limit: int = 50, offset: int = 0) -> dict:
        """
        Get all users with a specific role.
        
        Args:
            role: Role to filter by
            limit: Maximum number of users to return
            offset: Number of users to skip
            
        Returns:
            Dictionary with users and metadata
            
        Raises:
            ValueError: If invalid role
        """
        try:
            user_role = UserRole[role.upper()]
        except KeyError:
            raise ValueError(f"Invalid role: {role}")
        
        users = User.query.filter_by(role=user_role).limit(limit).offset(offset).all()
        total_count = User.query.filter_by(role=user_role).count()
        
        return {
            'role': role,
            'users': [
                {
                    'id': u.id,
                    'user_id': u.id,  # Keep for backward compatibility
                    'username': u.username,
                    'email': u.email,
                    'full_name': u.full_name,
                    'role': u.role.value,
                    'is_active': u.is_active,
                    'created_at': u.created_at.isoformat()
                }
                for u in users
            ],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }
    
    @staticmethod
    def deactivate_user(user_id: int, admin_id: int) -> dict:
        """
        Deactivate a user account (admin only).
        
        Args:
            user_id: ID of the user to deactivate
            admin_id: ID of the admin performing the action
            
        Returns:
            Dictionary with updated user data
            
        Raises:
            ValueError: If user not found
        """
        user = User.query.get(user_id)
        
        if not user:
            raise ValueError("User not found")
        
        try:
            user.is_active = False
            db.session.commit()
            
            log_audit(
                user_id=admin_id,
                action=AuditAction.ADMIN_ACTION,
                resource_type='user',
                resource_id=str(user_id),
                details=f'User deactivated: {user.username}'
            )
            
            return {
                'success': True,
                'user_id': user.id,
                'username': user.username,
                'is_active': user.is_active
            }
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Failed to deactivate user: {str(e)}")
    
    @staticmethod
    def activate_user(user_id: int, admin_id: int) -> dict:
        """
        Activate a user account (admin only).
        
        Args:
            user_id: ID of the user to activate
            admin_id: ID of the admin performing the action
            
        Returns:
            Dictionary with updated user data
            
        Raises:
            ValueError: If user not found
        """
        user = User.query.get(user_id)
        
        if not user:
            raise ValueError("User not found")
        
        try:
            user.is_active = True
            db.session.commit()
            
            log_audit(
                user_id=admin_id,
                action=AuditAction.ADMIN_ACTION,
                resource_type='user',
                resource_id=str(user_id),
                details=f'User activated: {user.username}'
            )
            
            return {
                'success': True,
                'user_id': user.id,
                'username': user.username,
                'is_active': user.is_active
            }
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"Failed to activate user: {str(e)}")
