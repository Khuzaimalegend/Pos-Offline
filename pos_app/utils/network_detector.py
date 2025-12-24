
import socket
import json
import os
from datetime import datetime

class NetworkDetector:
    def __init__(self):
        self.current_ip = None
        self.network_range = None
        self.config_path = os.path.join(os.path.dirname(__file__), 'config', 'database.json')
    
    def get_current_ip(self):
        """Get current local IP address"""
        try:
            # Method 1: Connect to external address to get local IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            try:
                # Method 2: Get hostname IP
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                if local_ip.startswith('127.'):
                    # Method 3: Get all interfaces
                    import subprocess
                    result = subprocess.run(['ipconfig'], capture_output=True, text=True)
                    lines = result.stdout.split('\n')
                    for i, line in enumerate(lines):
                        if 'IPv4 Address' in line and '192.168.' in line:
                            ip = line.split(':')[1].strip()
                            return ip
                return local_ip
            except:
                return "127.0.0.1"
    
    def detect_network_range(self, ip):
        """Detect network range based on IP"""
        if ip.startswith('192.168.'):
            return '192.168.0.0/16'
        elif ip.startswith('10.'):
            return '10.0.0.0/8'
        elif ip.startswith('172.'):
            octets = ip.split('.')
            if 16 <= int(octets[1]) <= 31:
                return '172.16.0.0/12'
        return '127.0.0.1/32'
    
    def update_database_config(self, mode='auto'):
        """Update database configuration based on current network"""
        self.current_ip = self.get_current_ip()
        self.network_range = self.detect_network_range(self.current_ip)
        
        print(f"[NetworkDetector] Current IP: {self.current_ip}")
        print(f"[NetworkDetector] Network Range: {self.network_range}")
        
        # Try to find PostgreSQL server on network
        postgresql_host = self.find_postgresql_server()
        
        config = {
            "username": "admin",
            "password": "admin",
            "host": postgresql_host,
            "port": "5432",
            "database": "pos_network",
            "connection_settings": {
                "pool_size": 5,
                "max_overflow": 10,
                "pool_timeout": 30,
                "pool_recycle": 3600,
                "connect_timeout": 10
            },
            "network_info": {
                "current_ip": self.current_ip,
                "network_range": self.network_range,
                "detected_at": datetime.now().isoformat(),
                "mode": mode
            },
            "description": f"Dynamic network configuration - Current IP: {self.current_ip}"
        }
        
        # Ensure config directory exists
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # Save configuration
        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        
        print(f"[NetworkDetector] Database config updated for {postgresql_host}:5432")
        return config
    
    def find_postgresql_server(self):
        """Find PostgreSQL server on network"""
        # First try localhost
        if self.test_postgresql_connection("localhost"):
            print("[NetworkDetector] Found PostgreSQL on localhost")
            return "localhost"
        
        # Try current IP (this machine)
        if self.current_ip != "127.0.0.1" and self.test_postgresql_connection(self.current_ip):
            print(f"[NetworkDetector] Found PostgreSQL on {self.current_ip}")
            return self.current_ip
        
        # Try common server IPs in the network
        if self.current_ip.startswith('192.168.'):
            network_base = '.'.join(self.current_ip.split('.')[:-1])
            common_ips = [f"{network_base}.1", f"{network_base}.100", f"{network_base}.10", f"{network_base}.50"]
            
            for ip in common_ips:
                if ip != self.current_ip and self.test_postgresql_connection(ip):
                    print(f"[NetworkDetector] Found PostgreSQL on {ip}")
                    return ip
        
        # Fallback to localhost
        print("[NetworkDetector] No network PostgreSQL found, using localhost")
        return "localhost"
    
    def test_postgresql_connection(self, host):
        """Test if PostgreSQL is accessible on given host"""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host=host,
                port=5432,
                database='postgres',
                user='admin',
                password='admin',
                connect_timeout=3
            )
            conn.close()
            return True
        except:
            try:
                # Try with postgres user
                conn = psycopg2.connect(
                    host=host,
                    port=5432,
                    database='postgres',
                    user='postgres',
                    password='admin',
                    connect_timeout=3
                )
                conn.close()
                return True
            except:
                return False

# Auto-detect network on import
if __name__ == "__main__":
    detector = NetworkDetector()
    detector.update_database_config()
