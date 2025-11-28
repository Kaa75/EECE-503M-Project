"""Script to seed the database with a default admin user."""
import os
from app import create_app, db
from app.models import User, UserRole
from app.security import hash_password

def seed_default_admin():
    """Create a default admin user if one doesn't exist."""
    config_name = os.getenv('FLASK_ENV', 'development')
    app = create_app(config_name)
    
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(username='admin').first()
        
        if admin:
            print("Default admin already exists!")
            print(f"Username: {admin.username}")
            return
        
        # Create default admin
        # Seed default admin with credential rotation requirement per spec
        admin = User(
            username='admin',
            email='admin@banking.com',
            phone='+1234567890',
            password_hash=hash_password('Admin@123'),
            full_name='System Administrator',
            role=UserRole.ADMIN,
            is_active=True,
            must_change_credentials=True
        )
        
        db.session.add(admin)
        db.session.commit()
        
        print("✅ Default admin created successfully!")
        print("=" * 50)
        print("Default Admin Credentials:")
        print("Username: admin")
        print("Password: Admin@123")
        print("=" * 50)
        print("⚠️  IMPORTANT: Please change these credentials after first login!")

if __name__ == '__main__':
    seed_default_admin()
