# Client-Server Authentication Architecture

## Problem Statement
In a client-server POS system, usernames and passwords are stored in the server's database. When a client PC tries to connect, it needs to authenticate before establishing a connection to the server. This creates a chicken-and-egg problem: how can the client authenticate without accessing the server database first?

## Solution: Local Authentication Cache

The POS application implements a hybrid authentication system that supports both online (server) and offline (local cache) authentication.

### How It Works

#### 1. **Server Authentication (Primary)**
When the server is available:
- Client sends username and password to the server
- Server validates credentials against the database
- If valid, user credentials are cached locally
- User is authenticated and gains access

```
Client → Server (validate) → Success → Cache locally → Access granted
```

#### 2. **Local Cache Authentication (Fallback)**
When the server is unavailable:
- Client attempts to authenticate using locally cached credentials
- If user has previously logged in, their hashed password is stored locally
- Client validates against the local cache
- User is authenticated with limited functionality

```
Client → Local Cache (validate) → Success → Access granted (offline mode)
```

### Cache Location
- **Windows**: `C:\Users\<username>\.pos_app\auth_cache\users_cache.json`
- **Linux**: `~/.pos_app/auth_cache/users_cache.json`
- **macOS**: `~/.pos_app/auth_cache/users_cache.json`

### Cache File Structure
```json
{
  "admin": {
    "password_hash": "salt:hashed_password",
    "is_admin": true,
    "full_name": "Administrator",
    "cached_at": "timestamp"
  },
  "worker1": {
    "password_hash": "salt:hashed_password",
    "is_admin": false,
    "full_name": "Worker One",
    "cached_at": "timestamp"
  }
}
```

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Login Attempt                             │
│              (Username + Password)                           │
└─────────────────────────────────────────────────────────────┘
                            ↓
                ┌───────────────────────┐
                │ Try Server Auth       │
                │ (Query Database)      │
                └───────────────────────┘
                            ↓
                    ┌───────┴───────┐
                    │               │
              Success          Failure/Timeout
                    │               │
                    ↓               ↓
            ┌──────────────┐  ┌──────────────────┐
            │ Cache User   │  │ Try Local Cache  │
            │ Credentials  │  │ (JSON File)      │
            └──────────────┘  └──────────────────┘
                    │               ↓
                    │         ┌─────┴──────┐
                    │         │            │
                    │     Success      Failure
                    │         │            │
                    └─────┬───┘            ↓
                          ↓        ┌──────────────┐
                    ┌──────────┐   │ Login Failed │
                    │ Granted  │   │ (Offline)    │
                    │ Access   │   └──────────────┘
                    └──────────┘
```

### Key Features

#### 1. **Automatic Credential Caching**
- After successful server authentication, credentials are automatically cached
- Hashed passwords are stored (never plain text)
- Cache is updated on each successful login

#### 2. **Offline Access**
- Users can log in even if the server is temporarily unavailable
- Works with cached credentials from previous logins
- Limited functionality in offline mode (no data sync)

#### 3. **Security**
- Passwords are hashed using SHA256 with salt
- Cache file is stored in user's home directory (protected by OS)
- No plain text passwords are ever stored
- Cache can be manually cleared if needed

#### 4. **Automatic Sync**
- When server connection is restored, credentials are synced
- New users are added to the cache
- Updated user information is reflected locally

### Implementation Details

#### LocalAuthCache Class (`pos_app/utils/local_auth.py`)

**Methods:**

1. **`cache_user_credentials(username, password_hash, is_admin, full_name)`**
   - Caches a user's credentials locally
   - Called after successful server authentication

2. **`authenticate_locally(username, password)`**
   - Authenticates using cached credentials
   - Returns user info if successful, None otherwise

3. **`sync_users_from_server(users_list)`**
   - Syncs user list from server to local cache
   - Called when server connection is established

4. **`clear_cache()`**
   - Clears all cached credentials
   - Used for logout or security purposes

#### Login Dialog Updates (`pos_app/views/login.py`)

The login process now:
1. Attempts server authentication first
2. If server is unavailable, falls back to local cache
3. Caches credentials after successful server login
4. Provides appropriate feedback to user

### Usage Examples

#### Server Authentication (Online)
```python
# User logs in with server available
# 1. Server validates credentials
# 2. Credentials are cached locally
# 3. User gains full access
```

#### Offline Authentication
```python
# User logs in with server unavailable
# 1. Local cache is checked
# 2. If user previously logged in, they can access offline
# 3. Limited functionality (no sync, no new data)
```

#### Manual Cache Management
```python
from pos_app.utils.local_auth import LocalAuthCache

# Clear all cached credentials
LocalAuthCache.clear_cache()

# Sync users from server
users = db_session.query(User).all()
LocalAuthCache.sync_users_from_server(users)
```

### Security Considerations

1. **Cache Location**: Cache is stored in user's home directory, protected by OS permissions
2. **Password Hashing**: Uses SHA256 with random salt (same as server)
3. **No Sync Issues**: Cache is read-only during offline mode
4. **Automatic Cleanup**: Old cache entries can be manually cleared

### Limitations

1. **Offline Mode**: Limited to cached data, no real-time sync
2. **New Users**: Cannot add new users in offline mode
3. **Password Changes**: Must be done on server when online
4. **Data Freshness**: Cached data may be stale

### Best Practices

1. **Regular Sync**: Ensure regular connection to server for credential updates
2. **Cache Cleanup**: Periodically clear cache on shared machines
3. **Password Updates**: Change passwords regularly on the server
4. **Monitoring**: Log offline authentications for audit purposes

### Testing

#### Test Server Authentication
1. Start POS application with server running
2. Log in with valid credentials
3. Verify user is authenticated
4. Check cache file is created

#### Test Offline Authentication
1. Log in successfully with server (caches credentials)
2. Stop the server or disconnect network
3. Restart POS application
4. Log in with same credentials
5. Verify offline authentication works

#### Test Fallback
1. Start with server unavailable
2. Try to log in with cached credentials
3. Verify offline access is granted
4. Reconnect to server
5. Verify sync occurs

## Configuration

No additional configuration is required. The system automatically:
- Detects server availability
- Falls back to local cache when needed
- Syncs credentials when connection is restored

## Future Enhancements

1. **Encrypted Cache**: Encrypt cache file for additional security
2. **Expiring Credentials**: Auto-expire cached credentials after X days
3. **Audit Logging**: Log all offline authentications
4. **Partial Sync**: Sync only changed data when reconnecting
5. **Multi-Device**: Sync cache across multiple client devices
