"""
Authentication and permission tests

Tests cover:
- User login success/failure
- Password validation
- Role-based access control
- Admin vs Worker permissions
- Session management
"""

import pytest
from pos_app.models.database import User
from pos_app.utils.auth import hash_password, check_password


@pytest.mark.unit
class TestPasswordHashing:
    """Test password hashing and verification"""
    
    def test_password_hash_creates_different_hashes(self):
        """Test that same password creates different hashes"""
        password = "testpass123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Hashes should be different due to salt
        assert hash1 != hash2
    
    def test_password_verification_success(self):
        """Test that correct password verifies successfully"""
        password = "testpass123"
        hashed = hash_password(password)
        
        assert check_password(password, hashed) is True
    
    def test_password_verification_failure(self):
        """Test that incorrect password fails verification"""
        password = "testpass123"
        wrong_password = "wrongpass456"
        hashed = hash_password(password)
        
        assert check_password(wrong_password, hashed) is False
    
    def test_empty_password_handling(self):
        """Test handling of empty passwords"""
        hashed = hash_password("")
        assert check_password("", hashed) is True
        assert check_password("nonempty", hashed) is False


@pytest.mark.integration
class TestUserAuthentication:
    """Test user authentication logic"""
    
    def test_admin_user_creation(self, db_session):
        """Test creating an admin user"""
        user = User(
            username="admintest",
            password_hash=hash_password("adminpass123"),
            full_name="Admin Test User",
            is_admin=True,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        retrieved = db_session.query(User).filter_by(username="admintest").first()
        assert retrieved is not None
        assert retrieved.is_admin is True
        assert check_password("adminpass123", retrieved.password_hash)
    
    def test_worker_user_creation(self, db_session):
        """Test creating a worker user"""
        user = User(
            username="workertest",
            password_hash=hash_password("workerpass123"),
            full_name="Worker Test User",
            is_admin=False,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        retrieved = db_session.query(User).filter_by(username="workertest").first()
        assert retrieved is not None
        assert retrieved.is_admin is False
    
    def test_inactive_user(self, db_session):
        """Test that inactive users are marked correctly"""
        user = User(
            username="inactivetest",
            password_hash=hash_password("inactivepass123"),
            full_name="Inactive Test User",
            is_admin=False,
            is_active=False
        )
        db_session.add(user)
        db_session.commit()
        
        retrieved = db_session.query(User).filter_by(username="inactivetest").first()
        assert retrieved.is_active is False
    
    def test_duplicate_username_constraint(self, db_session):
        """Test that duplicate usernames are prevented"""
        user1 = User(
            username="duplicate",
            password_hash=hash_password("pass1"),
            full_name="User 1",
            is_admin=False,
            is_active=True
        )
        db_session.add(user1)
        db_session.commit()
        
        user2 = User(
            username="duplicate",
            password_hash=hash_password("pass2"),
            full_name="User 2",
            is_admin=False,
            is_active=True
        )
        db_session.add(user2)
        
        from sqlalchemy.exc import IntegrityError
        with pytest.raises(IntegrityError):
            db_session.commit()


@pytest.mark.unit
class TestRoleBasedAccess:
    """Test role-based access control"""
    
    def test_admin_user_has_admin_flag(self, sample_admin_user):
        """Test that admin users have is_admin=True"""
        assert sample_admin_user.is_admin is True
    
    def test_regular_user_lacks_admin_flag(self, sample_regular_user):
        """Test that regular users have is_admin=False"""
        assert sample_regular_user.is_admin is False
    
    def test_user_active_status(self, db_session):
        """Test user active/inactive status"""
        active_user = User(
            username="activeuser",
            password_hash=hash_password("pass"),
            full_name="Active User",
            is_admin=False,
            is_active=True
        )
        
        inactive_user = User(
            username="inactiveuser",
            password_hash=hash_password("pass"),
            full_name="Inactive User",
            is_admin=False,
            is_active=False
        )
        
        db_session.add_all([active_user, inactive_user])
        db_session.commit()
        
        # Verify statuses
        active = db_session.query(User).filter_by(username="activeuser").first()
        inactive = db_session.query(User).filter_by(username="inactiveuser").first()
        
        assert active.is_active is True
        assert inactive.is_active is False


@pytest.mark.unit
class TestAccessControlDecorators:
    """Test access control decorator functionality"""
    
    def test_admin_required_decorator_exists(self):
        """Test that admin_required decorator is available"""
        try:
            from pos_app.utils.permissions import admin_required
            assert admin_required is not None
        except ImportError:
            pytest.skip("permissions module not available")
    
    def test_admin_required_decorator_callable(self):
        """Test that admin_required decorator is callable"""
        try:
            from pos_app.utils.permissions import admin_required
            
            @admin_required
            def test_function():
                return "success"
            
            assert callable(test_function)
        except ImportError:
            pytest.skip("permissions module not available")


@pytest.mark.integration
class TestUserManagement:
    """Test user management operations"""
    
    def test_create_user_in_database(self, db_session):
        """Test creating a user in database"""
        user = User(
            username="newuser",
            password_hash=hash_password("newpass123"),
            full_name="New User",
            is_admin=False,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        
        retrieved = db_session.query(User).filter_by(username="newuser").first()
        assert retrieved is not None
        assert retrieved.full_name == "New User"
    
    def test_update_user_password(self, db_session, sample_admin_user):
        """Test updating user password"""
        new_password = "newpassword456"
        sample_admin_user.password_hash = hash_password(new_password)
        db_session.commit()
        
        retrieved = db_session.query(User).get(sample_admin_user.id)
        assert check_password(new_password, retrieved.password_hash)
    
    def test_update_user_role(self, db_session, sample_regular_user):
        """Test updating user role"""
        sample_regular_user.is_admin = True
        db_session.commit()
        
        retrieved = db_session.query(User).get(sample_regular_user.id)
        assert retrieved.is_admin is True
    
    def test_delete_user(self, db_session):
        """Test deleting a user"""
        user = User(
            username="deletetest",
            password_hash=hash_password("pass"),
            full_name="Delete Test",
            is_admin=False,
            is_active=True
        )
        db_session.add(user)
        db_session.commit()
        user_id = user.id
        
        db_session.delete(user)
        db_session.commit()
        
        retrieved = db_session.query(User).get(user_id)
        assert retrieved is None
    
    def test_query_all_users(self, db_session, sample_admin_user, sample_regular_user):
        """Test querying all users"""
        all_users = db_session.query(User).all()
        
        assert len(all_users) >= 2
        usernames = [u.username for u in all_users]
        assert sample_admin_user.username in usernames
        assert sample_regular_user.username in usernames
    
    def test_query_admin_users_only(self, db_session, sample_admin_user, sample_regular_user):
        """Test querying only admin users"""
        admin_users = db_session.query(User).filter_by(is_admin=True).all()
        
        assert len(admin_users) >= 1
        assert sample_admin_user in admin_users
        assert sample_regular_user not in admin_users
    
    def test_query_active_users_only(self, db_session):
        """Test querying only active users"""
        active_user = User(
            username="activeonly",
            password_hash=hash_password("pass"),
            full_name="Active Only",
            is_admin=False,
            is_active=True
        )
        
        inactive_user = User(
            username="inactiveonly",
            password_hash=hash_password("pass"),
            full_name="Inactive Only",
            is_admin=False,
            is_active=False
        )
        
        db_session.add_all([active_user, inactive_user])
        db_session.commit()
        
        active_users = db_session.query(User).filter_by(is_active=True).all()
        
        assert active_user in active_users
        assert inactive_user not in active_users


@pytest.mark.unit
class TestSessionManagement:
    """Test session and token management"""
    
    def test_user_last_login_tracking(self, db_session, sample_admin_user):
        """Test that last login can be tracked"""
        from datetime import datetime
        
        now = datetime.now()
        sample_admin_user.last_login = now
        db_session.commit()
        
        retrieved = db_session.query(User).get(sample_admin_user.id)
        assert retrieved.last_login is not None
    
    def test_user_last_activity_tracking(self, db_session, sample_admin_user):
        """Test that last activity can be tracked"""
        from datetime import datetime
        
        now = datetime.now()
        sample_admin_user.last_activity = now
        db_session.commit()
        
        retrieved = db_session.query(User).get(sample_admin_user.id)
        assert retrieved.last_activity is not None
