# POS Application Login Instructions

## Starting the Application

To start the POS application, run:

```bash
cd pos_app
python main.py
```

## Login Screen

When you start the application, a login dialog will appear with the following fields:

- **Username**: Enter your username
- **Password**: Enter your password

## Default Admin Account

For the first login, use the default admin credentials:

- **Username**: `admin`
- **Password**: `admin123`

## Authentication Methods

The application supports two authentication methods:

### 1. Server Authentication (Primary)
- When the server is available, credentials are validated against the PostgreSQL database
- After successful login, credentials are automatically cached locally
- This is the preferred method for security and data consistency

### 2. Offline Authentication (Fallback)
- If the server is unavailable, the application will attempt to authenticate using cached credentials
- This allows users to continue working even if the server is temporarily down
- Cached credentials are stored securely in the user's home directory

## Login Process

```
1. Enter username and password
2. Click "Login" button
3. Application attempts server authentication
   ├─ If server is available: Validate against database
   │  └─ Success: Cache credentials and grant access
   │  └─ Failure: Show error message
   └─ If server is unavailable: Try local cache
      └─ Success: Grant offline access
      └─ Failure: Show error message
```

## User Roles

After logging in, your access level depends on your user role:

### Administrator
- Full access to all features
- Can manage users (add, edit, delete)
- Can access financial reports and analytics
- Can configure system settings

### Worker
- Limited access to core POS features
- Can process sales and inventory
- Cannot manage users
- Cannot access financial reports
- Cannot modify system settings

## Creating New Users

Only administrators can create new users:

1. Log in as admin
2. Go to **Settings** → **Users** tab
3. Click **➕ Add User**
4. Fill in the user details:
   - Username (required)
   - Full Name (optional)
   - Password (required)
   - Confirm Password (required)
   - Role: Select "Administrator" for admin, leave unchecked for worker
5. Click **OK** to create the user

## Editing Users

To edit an existing user:

1. Go to **Settings** → **Users** tab
2. Select the user from the table
3. Click **✏️ Edit Selected**
4. Modify the details:
   - Full Name
   - Password (leave blank to keep current)
   - Role
   - Status (Active/Inactive)
5. Click **Save** to update

## Deleting Users

To delete a user:

1. Go to **Settings** → **Users** tab
2. Select the user from the table
3. Click **🗑️ Delete Selected**
4. Confirm the deletion
5. The user will be removed from the system

**Note**: You cannot delete your own account

## Troubleshooting

### "Invalid username or password"
- Check that you entered the correct username and password
- Ensure Caps Lock is not on
- If you forgot the password, contact an administrator

### "Server authentication failed"
- The server may be temporarily unavailable
- The application will attempt to use cached credentials
- If you haven't logged in before, you won't be able to access the system offline

### "Account is disabled"
- Your account has been deactivated by an administrator
- Contact an administrator to reactivate your account

### Login dialog doesn't appear
- Ensure the application is properly installed
- Check that all required dependencies are installed
- Try restarting the application

## Security Tips

1. **Change Default Password**: After first login, change the admin password
2. **Strong Passwords**: Use strong, unique passwords for each user
3. **Regular Updates**: Keep the application updated with the latest security patches
4. **Logout**: Always logout when leaving your workstation
5. **Cache Management**: Periodically clear cached credentials on shared machines

## Offline Mode

When the server is unavailable:

- You can still log in with previously cached credentials
- You can access cached data and perform transactions
- Changes will be synced when the server comes back online
- New users cannot be created in offline mode
- Password changes must be done on the server

## Resetting Credentials

If you need to reset all cached credentials:

1. Delete the cache file:
   - **Windows**: `C:\Users\<username>\.pos_app\auth_cache\users_cache.json`
   - **Linux/Mac**: `~/.pos_app/auth_cache/users_cache.json`

2. Restart the application

3. Log in with your server credentials to rebuild the cache

## Support

For additional help or issues:

1. Check the application logs in the **Settings** → **System Info** tab
2. Contact your system administrator
3. Refer to the full documentation in `CLIENT_SERVER_AUTH.md`
