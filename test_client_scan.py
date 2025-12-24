#!/usr/bin/env python3
"""Test client mode scanning"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from pos_app.utils.ip_scanner import IPScanner
import socket

print("=" * 60)
print("CLIENT MODE SCANNING TEST")
print("=" * 60)

# Get local IP
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    local_ip = s.getsockname()[0]
    s.close()
    print(f"\n✅ Local IP: {local_ip}")
except Exception as e:
    print(f"❌ Error getting local IP: {e}")
    sys.exit(1)

# Get network base
scanner = IPScanner()
network_base = scanner.get_network_base()
print(f"✅ Network base: {network_base}")

# Scan for servers
print(f"\n🔍 Scanning {network_base}.1-254 for PostgreSQL servers...")
print("(This may take a minute...)")

found_servers = scanner.scan_network_range(1, 254, exclude_ip=None)

print(f"\n📊 Scan Results:")
print(f"   Total servers found: {len(found_servers)}")

if found_servers:
    print(f"\n   All servers found:")
    for server in found_servers:
        ip = server.get('ip')
        status = server.get('status')
        print(f"   - {ip}: {status}")
    
    # Filter out local IP
    external_servers = [s for s in found_servers if s.get('ip') != local_ip]
    print(f"\n   External servers (after filtering {local_ip}):")
    if external_servers:
        for server in external_servers:
            ip = server.get('ip')
            status = server.get('status')
            print(f"   - {ip}: {status}")
    else:
        print(f"   ❌ No external servers found (only found our own IP)")
else:
    print("❌ No PostgreSQL servers found on network")

print("\n" + "=" * 60)
