"""Network management utilities for server/client configuration."""

from __future__ import annotations

import json
import os
import socket
from datetime import datetime
from typing import Dict, Optional, Tuple

try:
    import psycopg2
except Exception:  # psycopg2 not available in some build contexts
    psycopg2 = None

from pos_app.utils.ip_scanner import IPScanner


CONFIG_DIR = os.path.join(os.path.dirname(__file__), '..', 'config')
DB_CONFIG_PATH = os.path.join(CONFIG_DIR, 'database.json')
NETWORK_CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'network_config.json')


def _ensure_config_dir():
    os.makedirs(CONFIG_DIR, exist_ok=True)


def _read_json(path: str) -> Dict:
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as exc:
        print(f"[network_manager] Failed to read {path}: {exc}")
    return {}


def _write_json(path: str, data: Dict):
    try:
        _ensure_config_dir()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
    except Exception as exc:
        print(f"[network_manager] Failed to write {path}: {exc}")


def detect_local_ip(default: str = '127.0.0.1') -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return default


def read_db_config() -> Dict:
    data = _read_json(DB_CONFIG_PATH)
    if not data:
        data = {
            "username": "admin",
            "password": "admin",
            "host": "localhost",
            "port": "5432",
            "database": "pos_network",
            "description": "Default configuration"
        }
    # Ensure port is a valid integer string; auto-fix bad values.
    try:
        int(str(data.get("port", "5432") or "5432"))
    except (TypeError, ValueError):
        print(f"[Network] Invalid port in database.json: {data.get('port')!r}, defaulting to '5432'")
        data["port"] = "5432"
        _write_json(DB_CONFIG_PATH, data)
    return data


def write_db_config(config: Dict):
    _write_json(DB_CONFIG_PATH, config)


def read_network_config() -> Dict:
    return _read_json(NETWORK_CONFIG_PATH)


def write_network_config(data: Dict):
    _write_json(NETWORK_CONFIG_PATH, data)


def test_connection(host: str, port: str = '5432', user: str = 'admin', password: str = 'admin', database: str = 'pos_network', timeout: int = 5) -> Tuple[bool, str]:
    if psycopg2 is None:
        return False, "psycopg2 not available"

    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            connect_timeout=timeout
        )
        conn.close()
        return True, "Connection successful"
    except Exception as exc:
        return False, str(exc)


def _prepare_local_server(host: str, port: str, database: str, username: str, password: str):
    """Ensure local PostgreSQL has DB/user and is open for LAN connections.

    This is what makes remote clients (192.168.x.x etc.) stop getting
    "no pg_hba.conf entry" errors.
    """
    if psycopg2 is None:
        return

    port = int(port)
    candidates = [
        (username, password),
        ("postgres", password),
        ("postgres", "postgres"),
        ("postgres", "admin"),
    ]

    for admin_user, admin_pass in candidates:
        try:
            conn = psycopg2.connect(
                host=host,
                port=port,
                user=admin_user,
                password=admin_pass,
                database="postgres",
                connect_timeout=5,
            )
            conn.autocommit = True
            cur = conn.cursor()

            # Ensure database exists
            try:
                cur.execute("SELECT 1 FROM pg_database WHERE datname=%s", (database,))
                if not cur.fetchone():
                    try:
                        cur.execute(f"CREATE DATABASE {database};")
                    except Exception:
                        pass
            except Exception:
                pass

            # Ensure role exists / password synced
            try:
                cur.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (username,))
                if not cur.fetchone():
                    try:
                        cur.execute("CREATE ROLE %s WITH LOGIN PASSWORD %s;", (username, password))
                    except Exception:
                        pass
                else:
                    try:
                        cur.execute("ALTER ROLE %s WITH LOGIN PASSWORD %s;", (username, password))
                    except Exception:
                        pass
            except Exception:
                pass

            # Grant DB privileges (best effort)
            try:
                cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {database} TO {username};")
            except Exception:
                pass

            # Try to open LAN access by editing postgresql.conf and pg_hba.conf
            try:
                cur.execute("SHOW data_directory;")
                row = cur.fetchone()
                if row and row[0]:
                    data_dir = row[0]
                    
                    # Configure postgresql.conf to listen on all interfaces
                    postgresql_conf_path = os.path.join(data_dir, "postgresql.conf")
                    if os.path.exists(postgresql_conf_path):
                        try:
                            with open(postgresql_conf_path, "r", encoding="utf-8", errors="ignore") as f:
                                postgresql_content = f.read()
                        except Exception:
                            postgresql_content = ""
                        
                        # Check if already configured
                        if "listen_addresses = '*'" not in postgresql_content:
                            try:
                                with open(postgresql_conf_path, "a", encoding="utf-8", errors="ignore") as f:
                                    f.write("\n# POS_AUTONET_CONFIG\n")
                                    f.write("listen_addresses = '*'  # Listen on all interfaces\n")
                                print("[Network] Configured PostgreSQL to listen on all interfaces")
                            except Exception as e:
                                print(f"[Network] Could not update postgresql.conf: {e}")
                    
                    # Configure pg_hba.conf for LAN access
                    hba_path = os.path.join(data_dir, "pg_hba.conf")
                    if os.path.exists(hba_path):
                        try:
                            with open(hba_path, "r", encoding="utf-8", errors="ignore") as f:
                                hba_content = f.read()
                        except Exception:
                            hba_content = ""

                        marker = "# POS_AUTONET_RULES"
                        if marker not in hba_content:
                            try:
                                with open(hba_path, "a", encoding="utf-8", errors="ignore") as f:
                                    f.write("\n" + marker + "\n")
                                    f.write("# Allow LAN clients for POS system\n")
                                    f.write("host    all             all             192.168.0.0/16          md5\n")
                                    f.write("host    all             all             10.0.0.0/8              md5\n")
                                    f.write("host    all             all             172.16.0.0/12           md5\n")
                                print("[Network] Configured pg_hba.conf for LAN access")
                            except Exception:
                                pass

                        # NOTE: pg_reload_conf() does NOT reload listen_addresses
                        # User MUST restart PostgreSQL service for listen_addresses to take effect
                        print("[Network] ⚠️ IMPORTANT: PostgreSQL must be RESTARTED for listen_addresses change to take effect!")
                        print("[Network] Please restart PostgreSQL service for network access to work")
                        
                        # Try reload anyway (won't help with listen_addresses but may help with other settings)
                        try:
                            cur.execute("SELECT pg_reload_conf();")
                            print("[Network] PostgreSQL configuration reload attempted")
                        except Exception:
                            pass
            except Exception:
                pass

            # Optional: test connection via LAN IP to make sure pg_hba works
            try:
                lan_ip = detect_local_ip()
                ok, msg = test_connection(lan_ip, str(port), username, password, database, timeout=5)
                if ok:
                    print(f"[Network] LAN access verified at {lan_ip}:{port}")
                else:
                    print(f"[Network] LAN test failed at {lan_ip}:{port}: {msg}")
            except Exception as exc:
                print(f"[Network] LAN self-test error: {exc}")

            cur.close()
            conn.close()
            return
        except Exception:
            continue


def set_server_mode(host_ip: Optional[str] = None, port: str = '5432', username: str = 'admin', password: str = 'admin', database: str = 'pos_network') -> Dict:
    """Configure this PC as a POS server accessible from network"""
    host_ip = host_ip or detect_local_ip()
    
    print(f"[Network] Configuring server mode on {host_ip}:{port}")
    
    # CRITICAL: Check if another server is already running on the network
    print(f"[Network] Checking if another server is already running on the network...")
    scanner = IPScanner()
    found_servers = scanner.scan_network_range(1, 254, exclude_ip=host_ip, simple_mode=True)
    
    if found_servers:
        other_servers = [s for s in found_servers if s.get('ip') != host_ip]
        if other_servers:
            error_msg = f"❌ ERROR: Another server is already running at {other_servers[0].get('ip')}!\n\n"
            error_msg += "Only ONE PC can be a server at a time.\n"
            error_msg += f"Please change that PC to Client mode first, then try again."
            print(f"[Network] {error_msg}")
            raise ValueError(error_msg)
    
    # Build config but DO NOT persist to file
    config = {
        "username": username,
        "password": password,
        "host": host_ip,  # Use network IP, not localhost
        "port": str(port),
        "database": database,
        "description": f"Server mode on {host_ip}:{port} (network accessible)"
    }

    # NOTE: Do NOT save to database.json or network_config.json - we want to re-scan on every startup
    # This ensures dynamic detection instead of cached IPs

    # Prepare PostgreSQL for network access
    print("[Network] Configuring PostgreSQL for network access...")
    # Always connect to localhost to configure, but configure for network access
    _prepare_local_server("localhost", str(port), database, username, password)
    
    # Test network accessibility
    print(f"[Network] Testing server accessibility from {host_ip}...")
    ok, msg = test_connection(host_ip, str(port), username, password, database, timeout=5)
    if ok:
        print(f"✅ Server successfully configured and accessible at {host_ip}:{port}")
        print(f"📡 Clients can now connect to this server using IP: {host_ip}")
    else:
        print(f"❌ Server configuration issue: {msg}")
        print("💡 PostgreSQL may need to be restarted for listen_addresses change to take effect")
        print("💡 Check PostgreSQL configuration and firewall settings")
        print("💡 If you just started the app, restart PostgreSQL service and try again")
    
    return config


def set_client_mode(server_ip: str, port: str = '5432', username: str = 'admin', password: str = 'admin', database: str = 'pos_network') -> Dict:
    # Safety check: never connect to localhost or 127.0.0.1 in client mode
    if server_ip in ('localhost', '127.0.0.1'):
        print(f"[NETWORK] ⚠️ WARNING: Attempted to set client mode to {server_ip}, this is not allowed!")
        raise ValueError(f"Cannot connect to {server_ip} in client mode - must be external server")
    
    # Build config but DO NOT persist to file
    config = {
        "username": username,
        "password": password,
        "host": server_ip,
        "port": str(port),
        "database": database,
        "description": f"Client mode connected to {server_ip}:{port}"
    }

    # NOTE: Do NOT save to database.json or network_config.json - we want to re-scan on every startup
    # This ensures dynamic detection instead of cached IPs
    return config


def scan_for_server(start: int = 1, end: int = 150) -> Optional[Dict]:
    scanner = IPScanner()
    quick = scanner.quick_scan_common_ips()
    if quick and quick.get('status') == 'postgresql_found':
        return quick

    found = scanner.scan_network_range(start, end)
    best = scanner.get_best_server()
    return best


def bootstrap_database_config(force_update=False):
    """Bootstrap database configuration with priority: Client > Server > Offline"""
    print("[BOOTSTRAP] Starting database configuration...")
    
    # Always force discovery - never read from file
    print("[BOOTSTRAP] Starting fresh network discovery (no file caching)...")
    
    # Get local IP to avoid connecting to ourselves
    local_ip = detect_local_ip()
    print(f"[NETWORK] Local IP detected: {local_ip}")
    
    # PRIORITY 1: Try to find and connect to an EXTERNAL server as CLIENT
    print("[NETWORK] PRIORITY 1: Scanning for external PostgreSQL servers (CLIENT MODE)...")
    scanner = IPScanner()
    
    # Get local network base dynamically
    network_base = scanner.get_network_base()
    if not network_base:
        print("[NETWORK] Could not determine local network")
        network_base = None
    else:
        print(f"[SCAN] Scanning {network_base}.1-100 for PostgreSQL servers...")
    
    # Scan for servers - DO NOT exclude local IP yet, we'll filter after
    # Only scan first 100 IPs for faster detection
    print(f"[NETWORK] Scanning all IPs (will filter out local IP {local_ip} from results)")
    found_servers = scanner.scan_network_range(1, 100, exclude_ip=None)
    print(f"[NETWORK] Found {len(found_servers)} servers from scan")
    
    # If we found servers, try to connect to the first one that is NOT our own IP
    if found_servers:
        print(f"[NETWORK] Servers found: {[s.get('ip') for s in found_servers]}")
        
        # CRITICAL: Filter out our own IP - NEVER connect to ourselves in client mode
        external_servers = [s for s in found_servers if s.get('ip') != local_ip]
        print(f"[NETWORK] External servers after filtering local IP ({local_ip}): {[s.get('ip') for s in external_servers]}")
        
        if not external_servers:
            print(f"[NETWORK] ⚠️ Found servers but all are our own IP ({local_ip}), skipping CLIENT mode...")
            print(f"[NETWORK] This PC will become a SERVER instead")
        else:
            # Try to connect to each external server
            for server in external_servers:
                server_ip = server.get('ip')
                
                # CRITICAL SAFETY CHECK: Double-check it's not our IP
                if server_ip == local_ip:
                    print(f"[NETWORK] ⚠️ SAFETY CHECK: Skipping {server_ip} - it's our own IP!")
                    continue
                
                print(f"[NETWORK] Found external PostgreSQL server at {server_ip}, attempting CLIENT connection...")
                username = server.get('username', 'admin')
                password = server.get('password', 'admin')
                
                # Test connection to pos_network database first
                ok, msg = test_connection(server_ip, '5432', username, password, 'pos_network', timeout=5)
                if ok:
                    print(f"[NETWORK] ✅ Successfully connected to pos_network database at {server_ip}")
                    print(f"[NETWORK] ✅ CONFIGURED AS CLIENT (not server)")
                    config = set_client_mode(
                        server_ip=server_ip,
                        username=username,
                        password=password,
                        database='pos_network'
                    )
                    return config
                else:
                    # Try postgres database as fallback
                    ok, msg = test_connection(server_ip, '5432', username, password, 'postgres', timeout=5)
                    if ok:
                        print(f"[NETWORK] ✅ Connected to postgres database at {server_ip} (will use pos_network)")
                        print(f"[NETWORK] ✅ CONFIGURED AS CLIENT (not server)")
                        config = set_client_mode(
                            server_ip=server_ip,
                            username=username,
                            password=password,
                            database='pos_network'
                        )
                        return config
                    else:
                        print(f"[NETWORK] Could not connect to server at {server_ip}: {msg}, trying next...")
    
    # PRIORITY 2: Try to become a SERVER if PostgreSQL is running locally
    print("[NETWORK] PRIORITY 2: No external server found. Checking for local PostgreSQL (SERVER MODE)...")
    try:
        # Try different credential combinations
        credential_combinations = [
            ("admin", "admin"),         # Our default
            ("postgres", "postgres"),   # PostgreSQL default
            ("postgres", ""),           # Empty password
            ("postgres", "admin"),      # Mixed
        ]
        
        for user, password in credential_combinations:
            if test_connection("localhost", "5432", user, password, "postgres", timeout=2)[0]:
                print(f"[NETWORK] Found PostgreSQL on localhost with credentials: {user}/***")
                print(f"[NETWORK] ✅ CONFIGURED AS SERVER on {local_ip}")
                print(f"[NETWORK] This PC will HOST the database for other clients")
                config = set_server_mode(
                    host_ip=local_ip,
                    username=user,
                    password=password,
                    database='pos_network'
                )
                return config
        
        # If we get here, no valid credentials were found
        print("[NETWORK] ❌ No valid PostgreSQL credentials found on localhost")
        
    except Exception as e:
        print(f"[NETWORK] Failed to use localhost: {str(e)}")
    
    # PRIORITY 3: Fallback to OFFLINE mode
    print("[NETWORK] PRIORITY 3: No external server or local PostgreSQL found. Falling back to OFFLINE MODE")
    return {
        "host": "localhost",
        "port": "5432",
        "database": "pos_network",
        "username": "admin",
        "password": "admin",
        "offline_mode": True
    }


def get_current_mode() -> str:
    cfg = read_network_config()
    return cfg.get('mode', 'server')
