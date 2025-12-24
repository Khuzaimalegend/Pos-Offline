
import os
import json
import socket
import threading
import time
from datetime import datetime

def get_local_ip_safe():
    """Get local IP with comprehensive error handling"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(5)  # Add timeout
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception as e:
        print(f"[IP_DETECT] Could not get local IP: {e}")
        return "127.0.0.1"

def test_postgres_connection(host, port=5432, user="admin", password="admin", timeout=5):
    """Test PostgreSQL connection with timeout"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=host,
            port=port,
            database="postgres",  # Test with postgres database first
            user=user,
            password=password,
            connect_timeout=timeout
        )
        conn.close()
        return True
    except ImportError:
        print("[POSTGRES] psycopg2 not available - will use localhost fallback")
        return False
    except Exception as e:
        # Try with different credentials
        for alt_user, alt_pass in [("postgres", "admin"), ("postgres", "postgres"), ("pos_user", "admin")]:
            try:
                import psycopg2
                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    database="postgres",
                    user=alt_user,
                    password=alt_pass,
                    connect_timeout=timeout
                )
                conn.close()
                print(f"[POSTGRES] Found working credentials: {alt_user}")
                return {"user": alt_user, "password": alt_pass}
            except:
                continue
        return False

def scan_network_ips(start_ip=1, end_ip=150, max_workers=10):
    """Scan network range for PostgreSQL servers"""
    local_ip = get_local_ip_safe()
    network_base = '.'.join(local_ip.split('.')[:-1])

    print(f"[NETWORK_SCAN] Scanning {network_base}.{start_ip}-{end_ip} for PostgreSQL...")

    found_servers = []

    # Quick scan common IPs first
    common_ips = [f"{network_base}.{i}" for i in [1, 10, 50, 100, 150, 192]]

    for ip in common_ips:
        print(f"[SCAN] Testing {ip}...")
        result = test_postgres_connection(ip)
        if result:
            if isinstance(result, dict):
                found_servers.append({"ip": ip, "credentials": result})
            else:
                found_servers.append({"ip": ip, "credentials": {"user": "admin", "password": "admin"}})
            print(f"[SCAN] ✅ Found PostgreSQL at {ip}")

    if found_servers:
        return found_servers[0]  # Return best server

    # If no quick results, do background scan of full range
    def background_scan():
        for i in range(start_ip, min(end_ip + 1, 255)):  # Limit to valid IP range
            if i in [1, 10, 50, 100, 150, 192]:  # Skip already scanned
                continue

            ip = f"{network_base}.{i}"
            try:
                result = test_postgres_connection(ip, timeout=2)  # Shorter timeout for full scan
                if result:
                    server_info = {
                        "ip": ip,
                        "credentials": result if isinstance(result, dict) else {"user": "admin", "password": "admin"}
                    }
                    print(f"[SCAN] ✅ Found PostgreSQL at {ip} (background)")
                    update_database_config(server_info)
                    return
            except Exception as e:
                continue  # Continue scanning even if one IP fails

    # Start background scan
    scan_thread = threading.Thread(target=background_scan, daemon=True)
    scan_thread.start()

    return None  # Return None, will use localhost fallback

def update_database_config(server_info=None):
    """Update database configuration safely"""
    try:
        config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
        os.makedirs(config_dir, exist_ok=True)

        if server_info:
            # Use found server
            config = {
                "username": server_info["credentials"]["user"],
                "password": server_info["credentials"]["password"],
                "host": server_info["ip"],
                "port": "5432",
                "database": "pos_network",
                "connection_settings": {
                    "pool_size": 5,
                    "max_overflow": 10,
                    "pool_timeout": 30,
                    "pool_recycle": 3600,
                    "connect_timeout": 10
                },
                "auto_setup": {
                    "server_found": True,
                    "scan_completed": datetime.now().isoformat(),
                    "server_ip": server_info["ip"]
                },
                "description": f"Auto-configured for PostgreSQL at {server_info['ip']}"
            }
        else:
            # Localhost fallback
            config = {
                "username": "admin",
                "password": "admin",
                "host": "localhost",
                "port": "5432",
                "database": "pos_network",
                "connection_settings": {
                    "pool_size": 5,
                    "max_overflow": 10,
                    "pool_timeout": 30,
                    "pool_recycle": 3600,
                    "connect_timeout": 10
                },
                "auto_setup": {
                    "server_found": False,
                    "fallback_mode": True,
                    "scan_completed": datetime.now().isoformat()
                },
                "description": "Localhost fallback - no network PostgreSQL found"
            }

        config_path = os.path.join(config_dir, 'database.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

        print(f"[CONFIG] Database config updated for {config['host']}")

    except Exception as e:
        print(f"[CONFIG] Error updating config: {e}")

def run_ultimate_setup():
    """Run the ultimate setup process"""
    try:
        print("[SETUP] Starting ultimate auto-setup...")

        # Step 1: Detect local IP
        local_ip = get_local_ip_safe()
        print(f"[SETUP] Local IP detected: {local_ip}")

        # Step 2: Scan for PostgreSQL servers
        print("[SETUP] Scanning for PostgreSQL servers...")
        server_info = scan_network_ips(1, 150)

        # Step 3: Update configuration
        update_database_config(server_info)

        # Step 4: Test connection
        try:
            if server_info:
                test_result = test_postgres_connection(server_info["ip"])
                if test_result:
                    print(f"[SETUP] ✅ PostgreSQL connection test successful: {server_info['ip']}")
                else:
                    print(f"[SETUP] ❌ PostgreSQL connection test failed: {server_info['ip']}")
                    update_database_config(None)  # Fallback to localhost
            else:
                print("[SETUP] Using localhost fallback (no network PostgreSQL found)")
        except Exception as e:
            print(f"[SETUP] Connection test error: {e}")

        print("[SETUP] Ultimate auto-setup completed")

    except Exception as e:
        print(f"[SETUP] Ultimate setup error: {e}")
        print("[SETUP] Using emergency localhost configuration")
        update_database_config(None)
