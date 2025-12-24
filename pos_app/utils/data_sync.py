"""
Data Synchronization and Offline Caching System

This module handles:
1. Syncing data between client and server
2. Caching data locally for offline use
3. Detecting connection loss
4. Merging data when connection is restored
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import hashlib

class DataSync:
    """Handles data synchronization between client and server"""
    
    def __init__(self):
        self.cache_dir = os.path.expanduser("~/.pos_app/data_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        self.sync_log_path = os.path.join(self.cache_dir, "sync_log.json")
    
    def get_cache_file(self, table_name: str) -> str:
        """Get cache file path for a table"""
        return os.path.join(self.cache_dir, f"{table_name}_cache.json")
    
    def cache_table_data(self, table_name: str, data: List[Dict]) -> bool:
        """Cache table data locally for offline use"""
        try:
            cache_file = self.get_cache_file(table_name)
            cache_data = {
                "table": table_name,
                "data": data,
                "cached_at": datetime.now().isoformat(),
                "hash": self._hash_data(data)
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            
            print(f"[DataSync] Cached {len(data)} records from {table_name}")
            return True
        except Exception as e:
            print(f"[DataSync] Error caching {table_name}: {e}")
            return False
    
    def get_cached_data(self, table_name: str) -> Optional[List[Dict]]:
        """Get cached table data"""
        try:
            cache_file = self.get_cache_file(table_name)
            if not os.path.exists(cache_file):
                return None
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            print(f"[DataSync] Loaded {len(cache_data.get('data', []))} cached records from {table_name}")
            return cache_data.get('data', [])
        except Exception as e:
            print(f"[DataSync] Error reading cache for {table_name}: {e}")
            return None
    
    def is_cache_valid(self, table_name: str, max_age_minutes: int = 60) -> bool:
        """Check if cached data is still valid"""
        try:
            cache_file = self.get_cache_file(table_name)
            if not os.path.exists(cache_file):
                return False
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            cached_at = datetime.fromisoformat(cache_data.get('cached_at', ''))
            age_minutes = (datetime.now() - cached_at).total_seconds() / 60
            
            return age_minutes < max_age_minutes
        except Exception:
            return False
    
    def log_sync_event(self, event_type: str, table_name: str, details: str = ""):
        """Log synchronization events"""
        try:
            log_data = []
            if os.path.exists(self.sync_log_path):
                with open(self.sync_log_path, 'r', encoding='utf-8') as f:
                    log_data = json.load(f)
            
            log_data.append({
                "timestamp": datetime.now().isoformat(),
                "event": event_type,
                "table": table_name,
                "details": details
            })
            
            # Keep only last 1000 events
            log_data = log_data[-1000:]
            
            with open(self.sync_log_path, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[DataSync] Error logging sync event: {e}")
    
    def _hash_data(self, data: List[Dict]) -> str:
        """Generate hash of data for change detection"""
        try:
            data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
            return hashlib.md5(data_str.encode()).hexdigest()
        except Exception:
            return ""
    
    def detect_changes(self, table_name: str, current_data: List[Dict]) -> bool:
        """Detect if data has changed since last cache"""
        try:
            cache_file = self.get_cache_file(table_name)
            if not os.path.exists(cache_file):
                return True  # No cache = data changed
            
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            old_hash = cache_data.get('hash', '')
            new_hash = self._hash_data(current_data)
            
            return old_hash != new_hash
        except Exception:
            return True
    
    def merge_offline_changes(self, server_data: List[Dict], local_data: List[Dict], 
                             id_field: str = 'id') -> List[Dict]:
        """
        Merge offline changes with server data
        
        Strategy:
        - Server data is source of truth
        - Local changes are applied on top
        - Conflicts: server data wins (can be customized)
        """
        try:
            # Create dict of server data by ID
            server_dict = {item.get(id_field): item for item in server_data}
            
            # Apply local changes
            for local_item in local_data:
                item_id = local_item.get(id_field)
                if item_id not in server_dict:
                    # New item from offline mode
                    server_dict[item_id] = local_item
                else:
                    # Item exists on server - merge fields
                    # Keep server version but update non-conflicting fields
                    for key, value in local_item.items():
                        if key not in server_dict[item_id]:
                            server_dict[item_id][key] = value
            
            return list(server_dict.values())
        except Exception as e:
            print(f"[DataSync] Error merging data: {e}")
            return server_data
    
    def clear_cache(self, table_name: Optional[str] = None) -> bool:
        """Clear cache for a table or all tables"""
        try:
            if table_name:
                cache_file = self.get_cache_file(table_name)
                if os.path.exists(cache_file):
                    os.remove(cache_file)
                    print(f"[DataSync] Cleared cache for {table_name}")
            else:
                for file in os.listdir(self.cache_dir):
                    if file.endswith('_cache.json'):
                        os.remove(os.path.join(self.cache_dir, file))
                print(f"[DataSync] Cleared all caches")
            return True
        except Exception as e:
            print(f"[DataSync] Error clearing cache: {e}")
            return False


# Global instance
_data_sync = None

def get_data_sync() -> DataSync:
    """Get or create global DataSync instance"""
    global _data_sync
    if _data_sync is None:
        _data_sync = DataSync()
    return _data_sync
