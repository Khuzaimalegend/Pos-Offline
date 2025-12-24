
import os
import json
import socket
import threading
from datetime import datetime

def get_local_ip():
    """Get local IP safely"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def scan_ip_for_postgres(ip):
    """Scan single IP for PostgreSQL"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=ip, port=5432, database='postgres',
            user='admin', password='admin', connect_timeout=2
        )
        conn.close()
        return True
    except:
        try:
            conn = psycopg2.connect(
                host=ip, port=5432, database='postgres',
                user='postgres', password='admin', connect_timeout=2
            )
            conn.close()
            return True
        except:
            return False

def quick_scan_network():
    """Quick scan for PostgreSQL servers"""
    local_ip = get_local_ip()
    network_base = '.'.join(local_ip.split('.')[:-1])
    
    print(f"[SCAN] Scanning {network_base}.1-150 for PostgreSQL...")
    
    # Quick scan common IPs first
    common_ips = [f"{network_base}.{i}" for i in [1, 10, 50, 100, 150]]
    
    for ip in common_ips:
        if scan_ip_for_postgres(ip):
            print(f"[SCAN] Found PostgreSQL at {ip}")
            return ip
    
    # If no quick results, scan more IPs in background
    def background_scan():
        for i in range(1, 151):
            ip = f"{network_base}.{i}"
            if ip not in common_ips and scan_ip_for_postgres(ip):
                print(f"[SCAN] Found PostgreSQL at {ip}")
                update_config(ip)
                return
    
    # Start background scan
    thread = threading.Thread(target=background_scan, daemon=True)
    thread.start()
    
    return "localhost"  # Default fallback

def update_config(host="localhost"):
    """Update database configuration"""
    config = {
        "username": "admin",
        "password": "admin",
        "host": host,
        "port": "5432",
        "database": "pos_network",
        "connection_settings": {
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": 3600,
            "connect_timeout": 10
        },
        "description": f"Auto-configured for {host}"
    }
    
    config_dir = os.path.join(os.path.dirname(__file__), '..', 'config')
    os.makedirs(config_dir, exist_ok=True)
    
    config_path = os.path.join(config_dir, 'database.json')
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)
    
    print(f"[CONFIG] Database configured for {host}:5432")

def run_simple_setup():
    """Run simple setup process"""
    try:
        print("[SETUP] Running auto-setup...")
        
        # Scan for PostgreSQL
        postgres_host = quick_scan_network()
        
        # Update configuration
        update_config(postgres_host)
        
        print("[SETUP] Auto-setup completed")
        
    except Exception as e:
        print(f"[SETUP] Setup error: {e}")
        # Ensure localhost config exists
        update_config("localhost")
