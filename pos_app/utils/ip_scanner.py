
import socket
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

class IPScanner:
    def __init__(self):
        self.found_servers = []
        self.scan_results = {}
    
    def get_network_base(self):
        """Get network base (e.g., 192.168.1)"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            # Get network base (first 3 octets)
            parts = local_ip.split('.')
            return f"{parts[0]}.{parts[1]}.{parts[2]}"
        except:
            return "192.168.1"  # Default fallback
    
    def get_local_ip_last_octet(self):
        """Get the last octet of local IP"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            # Get last octet
            parts = local_ip.split('.')
            return parts[3]
        except:
            return "1"  # Default fallback
    
    def scan_ip_for_postgresql(self, ip, timeout=2):
        """Scan single IP for PostgreSQL"""
        try:
            import psycopg2
            
            # Try multiple user combinations
            credentials = [
                ('admin', 'admin'),
                ('postgres', 'admin'),
                ('postgres', 'postgres'),
                ('pos_user', 'admin')
            ]
            
            # Try different databases
            databases = ['pos_network', 'postgres', 'template1']
            
            for username, password in credentials:
                for database in databases:
                    try:
                        conn = psycopg2.connect(
                            host=ip,
                            port=5432,
                            database=database,
                            user=username,
                            password=password,
                            connect_timeout=timeout
                        )
                        conn.close()
                        
                        return {
                            'ip': ip,
                            'status': 'postgresql_found',
                            'username': username,
                            'password': password
                        }
                    except:
                        continue
            
            return {'ip': ip, 'status': 'no_postgresql'}
            
        except ImportError:
            # psycopg2 not available, try basic port check
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(timeout)
                result = sock.connect_ex((ip, 5432))
                sock.close()
                
                if result == 0:
                    return {'ip': ip, 'status': 'port_5432_open'}
                else:
                    return {'ip': ip, 'status': 'no_response'}
            except:
                return {'ip': ip, 'status': 'error'}
    
    def scan_network_range(self, start_ip=1, end_ip=150, max_workers=10, exclude_ip=None, simple_mode=False):
        """Scan IP range 1-150 for PostgreSQL servers (with reduced workers and timeout)"""
        network_base = self.get_network_base()
        
        print(f"[IPScanner] Scanning {network_base}.{start_ip}-{end_ip} for PostgreSQL (timeout: 1s per IP)...")
        if exclude_ip:
            print(f"[IPScanner] Excluding IP: {exclude_ip}")
        
        self.found_servers = []
        self.scan_results = {}
        
        # Create list of IPs to scan
        ips_to_scan = [f"{network_base}.{i}" for i in range(start_ip, end_ip + 1)]
        
        # Filter out excluded IP if provided
        if exclude_ip:
            ips_to_scan = [ip for ip in ips_to_scan if ip != exclude_ip]
        
        # Simple mode: scan sequentially without threading (more reliable)
        if simple_mode:
            print(f"[IPScanner] Using simple sequential scan mode...")
            for ip in ips_to_scan:
                result = self.scan_ip_for_postgresql(ip, timeout=2)
                if result.get('status') == 'postgresql_found':
                    self.found_servers.append(result)
                    print(f"[IPScanner] ✅ Found PostgreSQL at {ip}")
            print(f"[IPScanner] Scan complete. Found {len(self.found_servers)} PostgreSQL servers.")
            return self.found_servers
        
        # Scan with thread pool (reduced from 50 to 10 workers)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all scan tasks with 1 second timeout
            future_to_ip = {
                executor.submit(self.scan_ip_for_postgresql, ip, timeout=1): ip 
                for ip in ips_to_scan
            }
            
            # Collect results
            completed = 0
            for future in as_completed(future_to_ip):
                try:
                    result = future.result(timeout=3)
                    self.scan_results[result['ip']] = result
                    
                    if result['status'] == 'postgresql_found':
                        self.found_servers.append(result)
                        print(f"[IPScanner] ✅ Found PostgreSQL at {result['ip']} ({result['username']})")
                    
                    completed += 1
                    if completed % 25 == 0:
                        print(f"[IPScanner] Scanned {completed}/{len(ips_to_scan)} IPs...")
                        
                except Exception as e:
                    print(f"[IPScanner] Error scanning {future_to_ip.get(future, 'unknown')}: {e}")
        
        print(f"[IPScanner] Scan complete. Found {len(self.found_servers)} PostgreSQL servers.")
        return self.found_servers
    
    def get_best_server(self):
        """Get the best PostgreSQL server from scan results"""
        if not self.found_servers:
            return None
        
        # Prefer servers with 'admin' user
        admin_servers = [s for s in self.found_servers if s['username'] == 'admin']
        if admin_servers:
            return admin_servers[0]
        
        # Otherwise return first found
        return self.found_servers[0]
    
    def quick_scan_common_ips(self):
        """Quick scan of common server IPs"""
        network_base = self.get_network_base()
        common_ips = [f"{network_base}.{i}" for i in [1, 10, 50, 100, 150]]
        
        print(f"[IPScanner] Quick scanning common IPs: {common_ips}")
        
        for ip in common_ips:
            result = self.scan_ip_for_postgresql(ip, timeout=1)
            if result['status'] == 'postgresql_found':
                print(f"[IPScanner] ✅ Quick found PostgreSQL at {ip}")
                return result
        
        return None
