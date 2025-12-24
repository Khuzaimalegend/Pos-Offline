"""
Local Authentication Cache for Client-Server Architecture

This module handles offline authentication by caching user credentials locally.
When a client connects to a server, it can authenticate using cached credentials
before the server connection is established.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from pos_app.utils.auth import hash_password, check_password
from pos_app.utils.logger import app_logger


class LocalAuthCache:
    """Manages local authentication cache for offline/client-server scenarios"""
    
    CACHE_DIR = Path.home() / '.pos_app' / 'auth_cache'
    CACHE_FILE = CACHE_DIR / 'users_cache.json'
    
    @classmethod
    def ensure_cache_dir(cls):
        """Ensure cache directory exists"""
        cls.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def cache_user_credentials(cls, username: str, password_hash: str, is_admin: bool, full_name: str = None):
        """
        Cache user credentials locally for offline authentication
        
        Args:
            username: Username
            password_hash: Hashed password
            is_admin: Whether user is admin
            full_name: User's full name
        """
        try:
            cls.ensure_cache_dir()
            
            # Load existing cache
            cache = cls._load_cache()
            
            # Update or add user
            cache[username] = {
                'password_hash': password_hash,
                'is_admin': is_admin,
                'full_name': full_name or username,
                'cached_at': datetime.now().isoformat()
            }
            
            # Save cache
            with open(cls.CACHE_FILE, 'w') as f:
                json.dump(cache, f, indent=2)
            
            app_logger.info(f"Cached credentials for user: {username}")
            
        except Exception as e:
            app_logger.error(f"Failed to cache user credentials: {str(e)}")
    
    @classmethod
    def authenticate_locally(cls, username: str, password: str) -> dict:
        """
        Authenticate user using locally cached credentials
        
        Args:
            username: Username
            password: Plain text password
            
        Returns:
            Dictionary with user info if successful, None otherwise
        """
        try:
            cache = cls._load_cache()
            
            if username not in cache:
                app_logger.warning(f"User not found in local cache: {username}")
                return None
            
            user_data = cache[username]
            
            # Verify password
            if not check_password(password, user_data['password_hash']):
                app_logger.warning(f"Invalid password for user: {username}")
                return None
            
            app_logger.info(f"User authenticated locally: {username}")
            
            return {
                'username': username,
                'is_admin': user_data['is_admin'],
                'full_name': user_data['full_name'],
                'authenticated_locally': True
            }
            
        except Exception as e:
            app_logger.error(f"Local authentication failed: {str(e)}")
            return None
    
    @classmethod
    def sync_users_from_server(cls, users_list: list):
        """
        Sync user list from server to local cache
        
        Args:
            users_list: List of User objects from server
        """
        try:
            cls.ensure_cache_dir()
            cache = {}
            
            for user in users_list:
                cache[user.username] = {
                    'password_hash': user.password_hash,
                    'is_admin': user.is_admin,
                    'full_name': user.full_name or user.username,
                    'cached_at': None
                }
            
            with open(cls.CACHE_FILE, 'w') as f:
                json.dump(cache, f, indent=2)
            
            app_logger.info(f"Synced {len(users_list)} users to local cache")
            
        except Exception as e:
            app_logger.error(f"Failed to sync users from server: {str(e)}")
    
    @classmethod
    def _load_cache(cls) -> dict:
        """Load cache from file"""
        try:
            if cls.CACHE_FILE.exists():
                with open(cls.CACHE_FILE, 'r') as f:
                    return json.load(f)
        except Exception as e:
            app_logger.error(f"Failed to load cache: {str(e)}")
        
        return {}
    
    @classmethod
    def clear_cache(cls):
        """Clear all cached credentials"""
        try:
            if cls.CACHE_FILE.exists():
                cls.CACHE_FILE.unlink()
                app_logger.info("Local auth cache cleared")
        except Exception as e:
            app_logger.error(f"Failed to clear cache: {str(e)}")
