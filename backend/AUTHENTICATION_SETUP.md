# 🔐 Authentication Setup Guide

**Week 1 Day 2-3 & 4-5 Deliverable**

This guide explains how to set up and use the production-ready JWT authentication system.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Environment Setup](#environment-setup)
3. [Database Initialization](#database-initialization)
4. [Creating Admin User](#creating-admin-user)
5. [Using the API](#using-the-api)
6. [Security Considerations](#security-considerations)

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and update the `SECRET_KEY`:

```bash
# Generate a secure secret key
openssl rand -hex 32

# Add to .env
SECRET_KEY=<your-generated-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. Initialize Database

```bash
# Create database tables
python -c "from app.db import init_database, create_tables; init_database(); create_tables()"

# Seed initial admin user
python -m app.db.seed
```

### 4. Test Authentication

```bash
# Start the server
uvicorn app.main:app --reload

# Login with admin credentials
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

---

## 🔧 Environment Setup

### Required Environment Variables

Add these to your `.env` file:

```env
# JWT Authentication
SECRET_KEY=your-secret-key-here  # ⚠️ MUST be changed in production!
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database (for local development with SQLite)
ENV_STATE=local
SQLITE_DB_PATH=esg_copilot_dev.db
```

### Generating a Secure Secret Key

```bash
# Method 1: Using OpenSSL (recommended)
openssl rand -hex 32

# Method 2: Using Python
python -c "import secrets; print(secrets.token_hex(32))"
```

**⚠️ IMPORTANT**: Never commit your actual secret key to version control!

---

## 💾 Database Initialization

### Option 1: Automatic (Recommended)

The application automatically creates tables on startup if they don't exist:

```python
# In app/main.py startup event
create_tables()  # Creates all tables automatically
```

### Option 2: Manual

```bash
# Initialize database connection and create tables
python -c "from app.db import init_database, create_tables; init_database(); create_tables()"
```

### Verify Tables Created

```bash
# For SQLite (local development)
sqlite3 esg_copilot_dev.db ".tables"

# Expected output:
# users  conversations  conversation_messages  conversation_states
```

---

## 👤 Creating Admin User

### Option 1: Using Seed Script (Recommended)

```bash
python -m app.db.seed
```

This creates:
- **Admin User**: `admin` / `admin123`
- **Demo User**: `demo` / `demo123`

### Option 2: Using Registration API

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "secure_password_123",
    "full_name": "System Administrator"
  }'
```

Then manually update the user in the database to make them admin:

```sql
UPDATE users SET is_superuser = 1, role = 'admin' WHERE username = 'admin';
```

### ⚠️ Security Warning

**CHANGE THE DEFAULT ADMIN PASSWORD immediately after first login!**

---

## 📡 Using the API

### Authentication Endpoints

#### 1. Register New User

```bash
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "john",
  "email": "john@example.com",
  "password": "secure123",
  "full_name": "John Doe"
}

# Response
{
  "id": 1,
  "username": "john",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "role": "user",
  "created_at": "2025-01-10T10:00:00",
  "last_login": null
}
```

#### 2. Login

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "john",
  "password": "secure123"
}

# Response
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 3. Get Current User Info

```bash
GET /api/v1/auth/me
Authorization: Bearer <your-token>

# Response
{
  "id": 1,
  "username": "john",
  "email": "john@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_superuser": false,
  "role": "user",
  "created_at": "2025-01-10T10:00:00",
  "last_login": "2025-01-10T10:05:00"
}
```

#### 4. Logout

```bash
POST /api/v1/auth/logout
Authorization: Bearer <your-token>

# Response
{
  "message": "Successfully logged out",
  "detail": "Please discard your access token on the client side"
}
```

### Using Protected Endpoints

All other endpoints now require authentication:

```bash
# Example: Get knowledge stats
GET /api/v1/knowledge/stats
Authorization: Bearer <your-token>

# Without token or with invalid token:
# 401 Unauthorized: Could not validate credentials
```

### Example: Full Authentication Flow

```bash
# 1. Register
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"john","email":"john@example.com","password":"secure123","full_name":"John Doe"}')

# 2. Login
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"john","password":"secure123"}' \
  | jq -r '.access_token')

# 3. Use token for authenticated requests
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"

# 4. Use token for other endpoints
curl -X GET http://localhost:8000/api/v1/knowledge/stats \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🔒 Security Considerations

### Production Checklist

Before deploying to production:

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Change default admin password
- [ ] Set `ACCESS_TOKEN_EXPIRE_MINUTES` appropriately (e.g., 15-30 minutes)
- [ ] Use HTTPS for all API communications
- [ ] Consider implementing refresh tokens for longer sessions
- [ ] Set up rate limiting on login endpoint
- [ ] Enable CORS only for trusted domains
- [ ] Implement password complexity requirements
- [ ] Set up monitoring for failed login attempts
- [ ] Consider implementing 2FA for admin users

### Password Requirements

Current implementation:
- Minimum 8 characters
- Stored as bcrypt hash (industry standard)
- Passwords never sent in responses

Consider adding:
- Password complexity rules (uppercase, lowercase, numbers, special chars)
- Password history (prevent reuse)
- Password expiration policy
- Account lockout after failed attempts

### Token Security

Current implementation:
- JWT tokens with HS256 algorithm
- Configurable expiration (default: 30 minutes)
- Tokens verified on every request
- User fetched from database for each request

Best practices:
- Keep tokens short-lived
- Store tokens securely on client (httpOnly cookies or secure storage)
- Never log tokens
- Implement token blacklist for logout (optional, requires Redis/cache)

---

## 🧪 Testing

### Manual Testing

```bash
# Test registration
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"test","email":"test@example.com","password":"test1234","full_name":"Test User"}'

# Test login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test1234"}'

# Test invalid credentials
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"wrong_password"}'
# Expected: 401 Unauthorized

# Test protected endpoint without token
curl -X GET http://localhost:8000/api/v1/auth/me
# Expected: 403 Forbidden (missing credentials)

# Test protected endpoint with token
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <your-token>"
# Expected: User info
```

---

## 📚 Additional Resources

- **JWT Specification**: https://jwt.io/
- **Bcrypt Information**: https://en.wikipedia.org/wiki/Bcrypt
- **FastAPI Security**: https://fastapi.tiangolo.com/tutorial/security/
- **OWASP Authentication Guide**: https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html

---

## 🐛 Troubleshooting

### "Could not validate credentials" Error

**Cause**: Invalid or expired JWT token

**Solutions**:
1. Check token is being sent in `Authorization: Bearer <token>` format
2. Verify token hasn't expired (default: 30 minutes)
3. Ensure `SECRET_KEY` matches between token generation and verification
4. Login again to get a fresh token

### "User not found" Error

**Cause**: User doesn't exist in database or was deleted

**Solutions**:
1. Verify user exists: `SELECT * FROM users WHERE username = 'username';`
2. Re-register the user
3. Check database connection

### "Incorrect username or password" Error

**Cause**: Invalid login credentials

**Solutions**:
1. Verify username is correct (case-sensitive)
2. Verify password is correct
3. Check if user is active: `SELECT is_active FROM users WHERE username = 'username';`
4. Reset password if forgotten (use seed script or direct DB update)

### Tables Not Created

**Cause**: Models not imported before `create_tables()` call

**Solutions**:
1. Verify `app/db/__init__.py` imports all models
2. Run database initialization manually
3. Check database connection string
4. Verify file permissions (SQLite)

---

## ✅ Verification Checklist

After setup, verify everything works:

- [ ] Database tables created successfully
- [ ] Admin user created with correct credentials
- [ ] Can register a new user via API
- [ ] Can login and receive JWT token
- [ ] Can access `/auth/me` with valid token
- [ ] Cannot access `/auth/me` without token (401 error)
- [ ] Cannot login with invalid credentials (401 error)
- [ ] Token expires after configured time
- [ ] Last login timestamp updates on successful login

---

## 📝 Summary

You now have a production-ready authentication system with:

✅ **User Registration** - Secure user creation with validation
✅ **JWT Authentication** - Industry-standard token-based auth
✅ **Password Hashing** - Bcrypt for secure password storage
✅ **Role-Based Access Control** - User, admin, and superuser roles
✅ **Session Tracking** - Last login timestamps
✅ **Protected Endpoints** - All routes require authentication

**Next Steps**: Week 2 - Data Persistence (implement actual database storage for all services)
