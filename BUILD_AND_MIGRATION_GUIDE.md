# POS System - Build and Migration Guide

## Overview

This guide covers two main processes:
1. **Building the EXE** - Creating a standalone executable for distribution
2. **Database Migration** - Updating existing databases to the new schema

---

## Part 1: Building the EXE

### Prerequisites

Before building the EXE, ensure you have:
- Python 3.8 or later installed
- All dependencies installed: `pip install -r requirements.txt`
- Windows 7 or later (for the target system)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- **PySide6** - GUI framework
- **SQLAlchemy** - ORM for database
- **psycopg2-binary** - PostgreSQL driver
- **PyInstaller** - EXE builder
- And other required packages

### Step 2: Build the EXE

Run the build script:

```bash
python build_exe.py
```

The script will:
1. ✅ Check all dependencies
2. ✅ Clean previous builds
3. ✅ Create PyInstaller spec file
4. ✅ Build the executable
5. ✅ Create installer scripts
6. ✅ Generate documentation

### Step 3: Output Files

After successful build, you'll find:

```
dist/
├── POSSystem/                 # Main application folder
│   ├── POSSystem.exe         # Main executable
│   ├── _internal/            # Application libraries
│   └── ...
├── install.bat               # Automated installer
├── uninstall.bat             # Uninstaller
└── README.txt                # Installation instructions
```

### Step 4: Distribution

To distribute the application:

**Option A: Installer Method**
```bash
# Copy the entire dist folder to target machine
# Run: dist/install.bat as Administrator
```

**Option B: Portable Method**
```bash
# Copy dist/POSSystem folder to target machine
# Run: POSSystem.exe directly
```

---

## Part 2: Database Migration

### What is Database Migration?

Database migration updates your existing database schema to match the new application. It:
- ✅ Adds new columns to existing tables
- ✅ Preserves all existing data
- ✅ Creates missing tables if needed
- ✅ Logs all changes for audit trail

### Prerequisites

Before running migration:
- PostgreSQL must be running and accessible
- Database credentials must be correct
- Backup your database (recommended)

### Step 1: Run Migration Script

**On the new PC (before first run of application):**

```bash
python migration_new_pc.py
```

**On an existing PC (to upgrade database):**

```bash
python migration_new_pc.py
```

### Step 2: Migration Process

The script will:

1. **Connect to Database**
   - Reads configuration from `pos_app/config/database.json`
   - Connects to PostgreSQL server

2. **Update Tables**
   - Users table
   - Products table
   - Customers table
   - Sales table
   - Sale Items table
   - Inventory table
   - Expenses table
   - Suppliers table

3. **Add Columns**
   - Timestamps (created_at, updated_at)
   - Status fields
   - Additional metadata

4. **Preserve Data**
   - All existing data remains intact
   - New columns get default values
   - No data is deleted

5. **Log Changes**
   - Creates migration log in `migration_logs/` folder
   - Timestamp: `migration_YYYYMMDD_HHMMSS.log`

### Step 3: Verify Migration

After migration completes:

1. Check the log file for any warnings
2. Verify data in the database
3. Run the application to confirm it works

### Migration Log Example

```
[2025-12-10 15:30:00] [BOOTSTRAP] Starting database configuration...
[2025-12-10 15:30:01] Connecting to database at localhost:5432
[2025-12-10 15:30:02] ✅ Successfully connected to database
[2025-12-10 15:30:02] --- Migrating Users Table ---
[2025-12-10 15:30:03] ✅ Added column is_admin to users
[2025-12-10 15:30:03] ✅ Added column is_active to users
...
[2025-12-10 15:30:15] ✅ DATABASE MIGRATION COMPLETED SUCCESSFULLY
```

---

## Complete Workflow for New PC

### First Time Setup

1. **Install PostgreSQL** (if not already installed)
   ```bash
   # Download from https://www.postgresql.org/download/windows/
   # Or use: choco install postgresql
   ```

2. **Extract Application**
   ```bash
   # Extract dist/POSSystem to desired location
   ```

3. **Run Migration** (if upgrading from old database)
   ```bash
   python migration_new_pc.py
   ```

4. **Run Application**
   ```bash
   # Run POSSystem.exe
   # Or: python pos_app/main.py
   ```

5. **Enter License Key**
   - Default: `yallahmaA1!23`

### Subsequent Runs

- Simply run `POSSystem.exe`
- Application will auto-detect database configuration
- No additional setup needed

---

## Troubleshooting

### Build Issues

**Error: PyInstaller not found**
```bash
pip install PyInstaller
```

**Error: PySide6 not found**
```bash
pip install PySide6
```

**Build takes too long**
- This is normal for first build (5-10 minutes)
- Subsequent builds are faster

### Migration Issues

**Error: Cannot connect to database**
- Ensure PostgreSQL is running
- Check `pos_app/config/database.json` for correct credentials
- Verify network connectivity

**Error: Permission denied**
- Run migration script with administrator privileges
- Or ensure PostgreSQL user has proper permissions

**Error: Table does not exist**
- This is normal for new installations
- Migration will skip non-existent tables
- Application will create them on first run

### Application Issues

**Error: License key invalid**
- Use default key: `yallahmaA1!23`
- Or check license file in `%APPDATA%\POS_System\`

**Error: Cannot connect to database on startup**
- Application will run in OFFLINE MODE
- Check database configuration
- Run migration script if needed

---

## File Structure

```
POS/
├── build_exe.py              # EXE builder script
├── migration_new_pc.py        # Database migration script
├── requirements.txt           # Python dependencies
├── pos_app/
│   ├── main.py              # Application entry point
│   ├── config/
│   │   └── database.json    # Database configuration
│   ├── models/              # Database models
│   ├── views/               # GUI components
│   ├── controllers/         # Business logic
│   ├── utils/               # Utility functions
│   └── database/            # Database connection
├── dist/                    # Build output (created after build)
│   ├── POSSystem/
│   ├── install.bat
│   ├── uninstall.bat
│   └── README.txt
└── migration_logs/          # Migration logs (created after migration)
    └── migration_*.log
```

---

## Advanced Configuration

### Custom Database Connection

Edit `pos_app/config/database.json`:

```json
{
    "username": "admin",
    "password": "admin",
    "host": "192.168.1.100",
    "port": "5432",
    "database": "pos_network",
    "description": "Custom server configuration"
}
```

### Network Server Mode

The application automatically:
1. Tries to become a server on the local machine
2. Looks for existing servers on the network
3. Falls back to offline mode if needed

No manual configuration required!

---

## Support and Maintenance

### Regular Backups

```bash
# Backup PostgreSQL database
pg_dump -U admin -h localhost pos_network > backup_$(date +%Y%m%d).sql
```

### Restore from Backup

```bash
# Restore PostgreSQL database
psql -U admin -h localhost pos_network < backup_20251210.sql
```

### Check Application Logs

Logs are saved in:
- `pos_app/logs/` - Application logs
- `migration_logs/` - Migration logs
- `%APPDATA%\POS_System\` - License and settings

---

## Version Information

- **Application Version**: 1.0
- **Python Version**: 3.8+
- **PostgreSQL Version**: 12+
- **Build Date**: 2025-12-10

---

## License

This application is licensed under the terms specified in the license agreement.
Default License Key: `yallahmaA1!23`

---

## Contact

For support or questions, please contact the development team.
