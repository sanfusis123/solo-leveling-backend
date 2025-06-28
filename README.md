# Solo Leveling - Backend API

A powerful REST API backend for the Solo Leveling personal development tracker. Built with FastAPI, MongoDB, and modern Python practices.

## 🚀 Features

- **🔐 Secure Authentication**: JWT-based authentication with OAuth2
- **👥 User Management**: Admin approval system for new users
- **📅 Smart Calendar**: Event management with recurring events support
- **🎯 Progress Tracking**: Improvement logs and distraction monitoring
- **🧠 Flashcards System**: Spaced repetition for effective learning
- **📚 Learning Materials**: Organize and share educational content
- **✍️ Personal Diary**: Daily journaling with mood tracking
- **✨ Fun Zone**: Creative space for personal expression
- **📊 Analytics**: Comprehensive insights and productivity metrics
- **🛡️ Admin Panel**: User management and system monitoring

## 📋 Prerequisites

- Python 3.8 or higher
- MongoDB 4.4 or higher
- pip (Python package manager)

## 🛠️ Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd personal-dev-tracker
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the root directory:

```env
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
DB_NAME=personal_dev_tracker

# Security
SECRET_KEY=your-secret-key-here-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# CORS (for development)
FRONTEND_URL=http://localhost:3000

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

**Important**: Generate a secure secret key for production:
```python
import secrets
print(secrets.token_urlsafe(32))
```

### 5. Start MongoDB

Make sure MongoDB is running on your system:

```bash
# Windows (if installed as service)
net start MongoDB

# Linux/Mac
sudo systemctl start mongod

# Or run directly
mongod
```

## 🚀 Running the Application

### Development Mode

```bash
# Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using the main.py file
python main.py
```

### Production Mode

```bash
# With multiple workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Using Gunicorn (recommended)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 👤 Setting Up Admin User

After creating your first user through the registration process:

```bash
python scripts/make_first_user_admin.py
```

This will make the first registered user an admin with full privileges.

## 📚 API Documentation

Once the server is running, you can access:

- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/openapi.json

## 🔧 API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/users/` - User registration

### User Management
- `GET /api/v1/users/me` - Get current user
- `PUT /api/v1/users/me` - Update user (including password)

### Admin Endpoints (Requires Admin Role)
- `GET /api/v1/admin/users` - List all users
- `PUT /api/v1/admin/users/{id}/activate` - Activate user
- `PUT /api/v1/admin/users/{id}/deactivate` - Deactivate user
- `PUT /api/v1/admin/users/{id}/make-admin` - Grant admin privileges
- `DELETE /api/v1/admin/users/{id}` - Delete user
- `GET /api/v1/admin/stats` - System statistics

### Features
- `/api/v1/calendar/*` - Calendar and event management
- `/api/v1/improvement-log/*` - Progress tracking
- `/api/v1/flashcards/*` - Flashcard system
- `/api/v1/learning-materials/*` - Learning resources
- `/api/v1/diary/*` - Personal diary
- `/api/v1/fun-zone/*` - Creative content
- `/api/v1/analytics/*` - Analytics and insights

## 🏗️ Project Structure

```
personal-dev-tracker/
├── app/
│   ├── api/
│   │   ├── deps.py              # Dependencies (auth, etc.)
│   │   ├── deps_admin.py        # Admin dependencies
│   │   └── v1/
│   │       ├── api.py           # API router
│   │       └── endpoints/       # All endpoint modules
│   ├── core/
│   │   ├── config.py            # Configuration
│   │   ├── database.py          # Database connection
│   │   └── security.py          # Security utilities
│   ├── models/                  # Pydantic models
│   ├── schemas/                 # Request/Response schemas
│   └── main.py                  # FastAPI application
├── scripts/
│   └── make_first_user_admin.py # Admin setup script
├── .env                         # Environment variables
├── requirements.txt             # Python dependencies
└── README.md                    # This file
```

## 🔒 Security Features

- **Password Hashing**: Bcrypt with salt
- **JWT Tokens**: Secure token-based authentication
- **Admin Approval**: New users require admin activation
- **CORS Protection**: Configurable CORS settings
- **Input Validation**: Pydantic models for all inputs
- **Rate Limiting**: Can be added with slowapi

## 🗃️ Database Schema

The application uses MongoDB with the following collections:
- `users` - User accounts and authentication
- `events` - Calendar events
- `improvement_logs` - Progress tracking
- `flashcard_decks` & `flashcards` - Learning system
- `learning_materials` - Educational content
- `diary_entries` - Personal journal
- `fun_zone_content` - Creative content

## 🧪 Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest

# With coverage
pytest --cov=app tests/
```

## 📦 Deployment

### Using Docker

```dockerfile
FROM python:3.9

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Variables for Production

```env
MONGODB_URI=mongodb://username:password@host:port/database
SECRET_KEY=your-production-secret-key
FRONTEND_URL=https://your-frontend-domain.com
```

## 🐛 Troubleshooting

### Common Issues

1. **MongoDB Connection Error**
   - Ensure MongoDB is running
   - Check MONGODB_URI in .env file
   - Verify network connectivity

2. **Import Errors**
   - Activate virtual environment
   - Run `pip install -r requirements.txt`

3. **CORS Issues**
   - Update FRONTEND_URL in .env
   - Check allowed origins in config

4. **Authentication Errors**
   - Ensure SECRET_KEY is set
   - Check token expiration settings

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- FastAPI for the amazing framework
- MongoDB for the flexible database
- The Python community for excellent libraries