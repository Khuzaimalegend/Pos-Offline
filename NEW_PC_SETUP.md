# POS System - New PC Setup Guide

## Quick Start (Recommended)

### Step 1: Extract the EXE
1. Copy `POSSystem.exe` to your desired location (Desktop, Program Files, USB, etc.)
2. Double-click to run

### Step 2: First Run
On first run, the application will:
- Detect your local network
- Scan for existing PostgreSQL servers
- Create admin user automatically
- Show login screen

### Step 3: Login
**Default Credentials:**
- Username: `admin`
- Password: `admin`

---

## If Login Fails

### Issue: "Invalid username or password"

**Solution 1: Automatic Setup (Recommended)**
```bash
python setup_admin.py
```

This will:
- Create/verify the admin user
- Show current database configuration
- Display login credentials

**Solution 2: Manual Setup**

1. Ensure PostgreSQL is running on your network
2. Run the migration script:
   ```bash
   python migration_new_pc.py
   ```
3. Run the setup script:
   ```bash
   python setup_admin.py
   ```
4. Try logging in again with `admin` / `admin`

---

## Troubleshooting

### Problem: Application won't start

**Check 1: PostgreSQL Running**
- Ensure PostgreSQL is installed and running
- Or the application will use offline mode

**Check 2: Database Connection**
- The app auto-detects network servers
- If none found, it uses localhost
- If localhost not available, it uses offline mode

**Check 3: Logs**
- Check console output for error messages
- Look for `[ERROR]` or `[WARN]` messages

### Problem: Admin user not created

**Solution:**
```bash
python setup_admin.py
```

This script will:
- Create database tables if needed
- Create admin user if missing
- Show you the credentials

### Problem: Can't connect to database

**Check:**
1. PostgreSQL is running
2. Network connectivity is working
3. Database credentials in `pos_app/config/database.json`

**Fix:**
```bash
python migration_new_pc.py
```

---

## Default Credentials

| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `admin` |
| Role | Administrator |

---

## What Happens on First Run

1. **Database Detection**
   - Scans local network for PostgreSQL servers
   - Tries to connect to found servers
   - Falls back to localhost if available
   - Uses offline mode if no database found

2. **Table Creation**
   - Creates all necessary tables
   - Initializes schema

3. **Admin User Creation**
   - Creates default admin user if missing
   - Username: `admin`
   - Password: `admin`

4. **Demo Data**
   - Loads sample products, customers, suppliers
   - Helps you understand the system

---

## Files You Need

### Essential
- `POSSystem.exe` - Main application

### Optional (for setup/migration)
- `setup_admin.py` - Create admin user
- `migration_new_pc.py` - Update database schema
- `pos_app/config/database.json` - Database configuration

---

## Changing Admin Password

After first login:
1. Go to Settings
2. Find User Management
3. Change admin password
4. Save changes

---

## Network Setup

### Server Mode (Default)
- Application becomes a server
- Other PCs can connect to it
- Requires PostgreSQL running

### Client Mode
- Connects to another PC's server
- Automatic for non-admin users
- Configured in database settings

### Offline Mode
- No database connection
- Limited functionality
- Auto-enabled if no database available

---

## Support

If you encounter issues:

1. **Check logs** - Look for error messages in console
2. **Run setup_admin.py** - Ensures admin user exists
3. **Run migration_new_pc.py** - Updates database schema
4. **Check database** - Ensure PostgreSQL is running

---

## Quick Commands

```bash
# Create/verify admin user
python setup_admin.py

# Migrate database schema
python migration_new_pc.py

# Run application from source
python pos_app/main.py

# Run standalone EXE
POSSystem.exe
```

---

## Next Steps

1. ✅ Run the EXE
2. ✅ Login with `admin` / `admin`
3. ✅ Explore the application
4. ✅ Change admin password in Settings
5. ✅ Create additional users as needed

Enjoy using POS System! 🚀
