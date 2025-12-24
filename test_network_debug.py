#!/usr/bin/env python3
"""
Debug script to test network scanning and server discovery
"""
import sys
import os
import socket
import time

# Add project to path
sys.path.insert(0, os.path.dirname(__file__))

def test_local_ip():
    """Test local IP detection"""
    print("\n" + "="*60)
    print("TEST 1: Local IP Detection")
    print("="*60)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        print(f"✅ Local IP detected: {local_ip}")
        return local_ip
    except Exception as e:
        print(f"❌ Failed to detect local IP: {e}")
        return None

def test_postgresql_connection(host, port=5432):
    """Test PostgreSQL connection"""
    print(f"\n[TEST] Checking PostgreSQL on {host}:{port}...")
    try:
        import psycopg2
        
        credentials = [
            ('admin', 'admin'),
            ('postgres', 'postgres'),
            ('postgres', 'admin'),
        ]
        
        for user, password in credentials:
            try:
                conn = psycopg2.connect(
                    host=host,
                    port=port,
                    user=user,
                    password=password,
                    database='postgres',
                    connect_timeout=2
                )
                conn.close()
                print(f"✅ PostgreSQL found on {host} with {user}/{password}")
                return True, user, password
            except:
                continue
        
        print(f"❌ No PostgreSQL found on {host}")
        return False, None, None
    except ImportError:
        print("❌ psycopg2 not available")
        return False, None, None

def test_port_scan(ip, port=5432):
    """Test if port is open"""
    print(f"[TEST] Scanning {ip}:{port}...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((ip, port))
        sock.close()
        
        if result == 0:
            print(f"✅ Port {port} is OPEN on {ip}")
            return True
        else:
            print(f"❌ Port {port} is CLOSED on {ip}")
            return False
    except Exception as e:
        print(f"❌ Error scanning {ip}:{port}: {e}")
        return False

def test_ip_scanner():
    """Test IP scanner"""
    print("\n" + "="*60)
    print("TEST 2: IP Scanner")
    print("="*60)
    try:
        from pos_app.utils.ip_scanner import IPScanner
        
        scanner = IPScanner()
        local_ip = scanner.get_network_base()
        print(f"Network base: {local_ip}")
        
        if not local_ip:
            print("❌ Could not determine network base")
            return
        
        print(f"\nScanning {local_ip}.1-20 for PostgreSQL...")
        found = scanner.scan_network_range(1, 20, exclude_ip=None)
        
        if found:
            print(f"✅ Found {len(found)} servers:")
            for server in found:
                print(f"   - {server.get('ip')}: {server.get('status')}")
        else:
            print("❌ No servers found")
            
    except Exception as e:
        print(f"❌ IP Scanner error: {e}")
        import traceback
        traceback.print_exc()

def test_bootstrap():
    """Test bootstrap database config"""
    print("\n" + "="*60)
    print("TEST 3: Bootstrap Database Config")
    print("="*60)
    try:
        from pos_app.utils.network_manager import bootstrap_database_config
        
        print("Running bootstrap_database_config(force_update=True)...")
        config = bootstrap_database_config(force_update=True)
        
        print(f"\n✅ Bootstrap completed!")
        print(f"   Host: {config.get('host')}")
        print(f"   Port: {config.get('port')}")
        print(f"   Database: {config.get('database')}")
        print(f"   Description: {config.get('description')}")
        
    except Exception as e:
        print(f"❌ Bootstrap error: {e}")
        import traceback
        traceback.print_exc()

def test_database_json():
    """Test database.json file"""
    print("\n" + "="*60)
    print("TEST 4: database.json File")
    print("="*60)
    try:
        import json
        db_json_path = os.path.join(os.path.dirname(__file__), 'pos_app', 'config', 'database.json')
        
        if os.path.exists(db_json_path):
            with open(db_json_path, 'r') as f:
                config = json.load(f)
            print(f"✅ database.json exists:")
            print(f"   Host: {config.get('host', 'NOT SET')}")
            print(f"   Port: {config.get('port')}")
            print(f"   Database: {config.get('database')}")
        else:
            print(f"❌ database.json not found at {db_json_path}")
            
    except Exception as e:
        print(f"❌ Error reading database.json: {e}")

def main():
    print("\n" + "="*60)
    print("POS NETWORK DEBUG TEST SUITE")
    print("="*60)
    
    # Test 1: Local IP
    local_ip = test_local_ip()
    
    # Test 2: PostgreSQL on localhost
    print("\n" + "="*60)
    print("TEST 2: PostgreSQL Connection")
    print("="*60)
    ok, user, pwd = test_postgresql_connection("localhost")
    if ok:
        print(f"✅ PostgreSQL is running locally")
        # Test network access
        if local_ip:
            test_port_scan(local_ip)
            test_postgresql_connection(local_ip)
    else:
        print(f"❌ PostgreSQL is NOT running locally")
    
    # Test 3: IP Scanner
    test_ip_scanner()
    
    # Test 4: database.json
    test_database_json()
    
    # Test 5: Bootstrap
    test_bootstrap()
    
    print("\n" + "="*60)
    print("DEBUG TEST COMPLETE")
    print("="*60)

if __name__ == '__main__':
    main()
