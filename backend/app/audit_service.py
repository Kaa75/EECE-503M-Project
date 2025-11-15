from datetime import datetime
from app.models import AuditLog, AuditAction, User, UserRole, db

class AuditService:
    """Service for managing audit logs and security monitoring."""
    
    @staticmethod
    def get_audit_logs(limit: int = 50, offset: int = 0, action: str = None, 
                      user_id: int = None, start_date: datetime = None, 
                      end_date: datetime = None) -> dict:
        """
        Retrieve audit logs with optional filtering.
        
        Args:
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            action: Filter by action type
            user_id: Filter by user ID
            start_date: Filter by start date
            end_date: Filter by end date
            
        Returns:
            Dictionary with audit logs and metadata
        """
        query = AuditLog.query
        
        # Apply filters
        if action:
            try:
                audit_action = AuditAction[action.upper()]
                query = query.filter_by(action=audit_action)
            except KeyError:
                raise ValueError(f"Invalid action: {action}")
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        if start_date:
            query = query.filter(AuditLog.timestamp >= start_date)
        
        if end_date:
            query = query.filter(AuditLog.timestamp <= end_date)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).offset(offset).all()
        
        return {
            'logs': [
                {
                    'log_id': log.id,
                    'user_id': log.user_id,
                    'username': log.user.username if log.user else 'System',
                    'action': log.action.value,
                    'resource_type': log.resource_type,
                    'resource_id': log.resource_id,
                    'details': log.details,
                    'ip_address': log.ip_address,
                    'timestamp': log.timestamp.isoformat()
                }
                for log in logs
            ],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }
    
    @staticmethod
    def get_user_audit_logs(user_id: int, limit: int = 50, offset: int = 0) -> dict:
        """
        Get all audit logs for a specific user.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            
        Returns:
            Dictionary with user's audit logs
            
        Raises:
            ValueError: If user not found
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError("User not found")
        
        logs = AuditLog.query.filter_by(user_id=user_id).order_by(
            AuditLog.timestamp.desc()
        ).limit(limit).offset(offset).all()
        
        total_count = AuditLog.query.filter_by(user_id=user_id).count()
        
        return {
            'user_id': user_id,
            'username': user.username,
            'logs': [
                {
                    'log_id': log.id,
                    'action': log.action.value,
                    'resource_type': log.resource_type,
                    'resource_id': log.resource_id,
                    'details': log.details,
                    'ip_address': log.ip_address,
                    'timestamp': log.timestamp.isoformat()
                }
                for log in logs
            ],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }
    
    @staticmethod
    def get_login_attempts(user_id: int = None, limit: int = 50, offset: int = 0) -> dict:
        """
        Get login attempts (successful and failed).
        
        Args:
            user_id: Optional filter by user ID
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            
        Returns:
            Dictionary with login attempt logs
        """
        query = AuditLog.query.filter(
            (AuditLog.action == AuditAction.LOGIN) |
            (AuditLog.action == AuditAction.LOGIN_FAILED)
        )
        
        if user_id:
            query = query.filter_by(user_id=user_id)
        
        total_count = query.count()
        
        logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).offset(offset).all()
        
        return {
            'logs': [
                {
                    'log_id': log.id,
                    'user_id': log.user_id,
                    'username': log.user.username if log.user else 'Unknown',
                    'action': log.action.value,
                    'details': log.details,
                    'ip_address': log.ip_address,
                    'timestamp': log.timestamp.isoformat()
                }
                for log in logs
            ],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }
    
    @staticmethod
    def get_suspicious_activities(limit: int = 50, offset: int = 0) -> dict:
        """
        Get all suspicious activities logged in the system.
        
        Args:
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            
        Returns:
            Dictionary with suspicious activity logs
        """
        logs = AuditLog.query.filter_by(action=AuditAction.SUSPICIOUS_ACTIVITY).order_by(
            AuditLog.timestamp.desc()
        ).limit(limit).offset(offset).all()
        
        total_count = AuditLog.query.filter_by(action=AuditAction.SUSPICIOUS_ACTIVITY).count()
        
        return {
            'logs': [
                {
                    'log_id': log.id,
                    'user_id': log.user_id,
                    'username': log.user.username if log.user else 'Unknown',
                    'action': log.action.value if log.action else None,
                    'resource_type': log.resource_type,
                    'resource_id': log.resource_id,
                    'details': log.details,
                    'ip_address': log.ip_address,
                    'timestamp': log.timestamp.isoformat()
                }
                for log in logs
            ],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }
    
    @staticmethod
    def get_admin_actions(limit: int = 50, offset: int = 0) -> dict:
        """
        Get all admin actions.
        
        Args:
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            
        Returns:
            Dictionary with admin action logs
        """
        logs = AuditLog.query.filter_by(action=AuditAction.ADMIN_ACTION).order_by(
            AuditLog.timestamp.desc()
        ).limit(limit).offset(offset).all()
        
        total_count = AuditLog.query.filter_by(action=AuditAction.ADMIN_ACTION).count()
        
        return {
            'logs': [
                {
                    'log_id': log.id,
                    'user_id': log.user_id,
                    'username': log.user.username if log.user else 'System',
                    'action': log.action.value if log.action else None,
                    'resource_type': log.resource_type,
                    'resource_id': log.resource_id,
                    'details': log.details,
                    'ip_address': log.ip_address,
                    'timestamp': log.timestamp.isoformat()
                }
                for log in logs
            ],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }
    
    @staticmethod
    def get_account_freeze_logs(limit: int = 50, offset: int = 0) -> dict:
        """
        Get all account freeze/unfreeze actions.
        
        Args:
            limit: Maximum number of logs to return
            offset: Number of logs to skip
            
        Returns:
            Dictionary with account freeze logs
        """
        query = AuditLog.query.filter(
            (AuditLog.action == AuditAction.ACCOUNT_FREEZE) |
            (AuditLog.action == AuditAction.ACCOUNT_UNFREEZE)
        )
        
        total_count = query.count()
        
        logs = query.order_by(AuditLog.timestamp.desc()).limit(limit).offset(offset).all()
        
        return {
            'logs': [
                {
                    'log_id': log.id,
                    'user_id': log.user_id,
                    'username': log.user.username if log.user else 'System',
                    'action': log.action.value,
                    'resource_id': log.resource_id,
                    'details': log.details,
                    'timestamp': log.timestamp.isoformat()
                }
                for log in logs
            ],
            'total_count': total_count,
            'limit': limit,
            'offset': offset
        }
