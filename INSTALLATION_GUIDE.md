# 🚀 Installation Guide - Latest Versions (November 2024)

## ✅ Prerequisites

### Python Version
- **Recommended**: Python 3.11 or 3.12
- **Minimum**: Python 3.10
- **Not supported**: Python < 3.10

Check your version:
```bash
python --version
# or
python3 --version
```

### Install Python 3.11+ (if needed)

**On Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
```

**On macOS:**
```bash
brew install python@3.11
```

**On Windows:**
Download from https://www.python.org/downloads/

---

## 📦 Installation Options

### Option 1: Standard Installation (Recommended)

```bash
# 1. Navigate to project directory
cd ai-coaching-backend

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# 4. Upgrade pip to latest
pip install --upgrade pip setuptools wheel

# 5. Install all dependencies
pip install -r requirements.txt

# If you get any errors, try:
pip install -r requirements-minimal.txt
```

### Option 2: Quick Minimal Installation

```bash
# Create and activate venv
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate    # Windows

# Install minimal dependencies
pip install --upgrade pip
pip install -r requirements-minimal.txt
```

### Option 3: Docker Installation (No Python Setup Needed)

```bash
# Make sure Docker is installed
docker --version

# Build and run
docker-compose up --build

# Access API at: http://localhost:8000
```

---

## 🔧 Package Versions (Latest as of Nov 2024)

### Core Packages:
- **FastAPI**: 0.115+ (latest stable)
- **Uvicorn**: 0.32+ (ASGI server)
- **SQLAlchemy**: 2.0.36+ (ORM)
- **Pydantic**: 2.10+ (validation)
- **Alembic**: 1.14+ (migrations)

### AI Packages:
- **OpenAI**: 1.57+ (GPT-4 support)
- **Anthropic**: 0.40+ (Claude support)

### Payment:
- **Stripe**: 11.2+ (latest API)

### Cloud Services:
- **Boto3**: 1.35+ (AWS S3)

---

## 🐛 Troubleshooting Common Issues

### Issue 1: "No module named 'email-validator'"

**Solution:**
```bash
pip install email-validator>=2.2.0
```

### Issue 2: "error: Microsoft Visual C++ 14.0 or greater is required" (Windows)

**Solution:**
```bash
# Install Microsoft C++ Build Tools
# Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/

# Or install pre-built wheels:
pip install --only-binary :all: cryptography bcrypt
```

### Issue 3: "Failed building wheel for cryptography"

**Linux:**
```bash
sudo apt-get update
sudo apt-get install build-essential libssl-dev libffi-dev python3-dev
pip install cryptography
```

**macOS:**
```bash
brew install openssl
pip install cryptography
```

**Windows:**
```bash
pip install --upgrade pip setuptools wheel
pip install cryptography --only-binary :all:
```

### Issue 4: "bcrypt" installation fails

**Linux:**
```bash
sudo apt-get install build-essential python3-dev
pip install bcrypt
```

**macOS:**
```bash
xcode-select --install
pip install bcrypt
```

### Issue 5: Package conflicts or dependency errors

**Solution:**
```bash
# Clear pip cache
pip cache purge

# Reinstall with no cache
pip install --no-cache-dir -r requirements.txt

# Or install one by one:
pip install fastapi uvicorn sqlalchemy pymysql python-dotenv pydantic
```

---

## 📋 Step-by-Step Verified Installation

### 1. System Preparation

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3-pip python3-venv python3-dev build-essential libssl-dev libffi-dev
```

**macOS:**
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Install Homebrew (if not installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**Windows:**
- Install Python 3.11+ from python.org
- Check "Add Python to PATH" during installation

### 2. Create Project Environment

```bash
# Clone or navigate to project
cd ai-coaching-backend

# Create virtual environment
python3 -m venv venv

# Activate (choose your OS)
source venv/bin/activate           # Linux/Mac
venv\Scripts\activate              # Windows CMD
venv\Scripts\Activate.ps1          # Windows PowerShell
```

### 3. Upgrade Core Tools

```bash
python -m pip install --upgrade pip
pip install --upgrade setuptools wheel
```

### 4. Install Dependencies

**Try Method 1 (Recommended):**
```bash
pip install -r requirements.txt
```

**If errors occur, try Method 2:**
```bash
pip install -r requirements-minimal.txt
```

**If still failing, try Method 3 (Manual):**
```bash
# Core framework
pip install "fastapi>=0.115.0"
pip install "uvicorn[standard]>=0.32.0"
pip install "python-multipart>=0.0.12"

# Database
pip install "sqlalchemy>=2.0.36"
pip install "alembic>=1.14.0"
pip install "pymysql>=1.1.1"

# Validation & Settings
pip install "pydantic>=2.10.3"
pip install "pydantic-settings>=2.6.1"
pip install "python-dotenv>=1.0.1"
pip install "email-validator>=2.2.0"

# Authentication
pip install "python-jose[cryptography]>=3.3.0"
pip install "passlib[bcrypt]>=1.7.4"
pip install "authlib>=1.3.2"
pip install "httpx>=0.28.0"

# Payment
pip install "stripe>=11.2.0"

# AWS S3
pip install "boto3>=1.35.70"

# AI (optional)
pip install "openai>=1.57.0"
pip install "anthropic>=0.40.0"

# Utilities
pip install "python-dateutil>=2.9.0"
pip install "psutil>=6.1.0"
```

### 5. Verify Installation

```bash
# Check installed packages
pip list

# Test imports
python -c "import fastapi; print(f'FastAPI {fastapi.__version__}')"
python -c "import sqlalchemy; print(f'SQLAlchemy {sqlalchemy.__version__}')"
python -c "import pydantic; print(f'Pydantic {pydantic.__version__}')"

# Test the application
python -c "from app.main import app; print('✅ All imports successful!')"
```

---

## 🐳 Docker Installation (Easiest Method)

### Prerequisites:
- Docker Desktop installed
- Docker Compose installed

### Steps:

```bash
# 1. Navigate to project
cd ai-coaching-backend

# 2. Build the image
docker-compose build

# 3. Start services
docker-compose up

# 4. Access API
# http://localhost:8000
# http://localhost:8000/docs (Swagger UI)
```

### Docker Benefits:
✅ No Python installation required
✅ No dependency conflicts
✅ Consistent environment
✅ Easy deployment
✅ Includes MySQL and Redis

---

## 🔍 Verify Everything Works

```bash
# 1. Check Python version
python --version
# Should show: Python 3.10+ or higher

# 2. Check virtual environment is active
which python
# Should show path to venv/bin/python

# 3. List installed packages
pip list | grep -E "fastapi|uvicorn|sqlalchemy|pydantic"

# 4. Test FastAPI import
python -c "from fastapi import FastAPI; app = FastAPI(); print('✅ FastAPI works!')"

# 5. Test all major imports
python << EOF
from fastapi import FastAPI
from sqlalchemy import create_engine
from pydantic import BaseModel
import stripe
import openai
print("✅ All core packages working!")
EOF
```

---

## 📦 Package Details

### Latest Versions (as of November 2024):

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.115+ | Web framework |
| uvicorn | 0.32+ | ASGI server |
| sqlalchemy | 2.0.36+ | Database ORM |
| pydantic | 2.10+ | Data validation |
| alembic | 1.14+ | DB migrations |
| openai | 1.57+ | GPT-4 API |
| anthropic | 0.40+ | Claude API |
| stripe | 11.2+ | Payments |
| boto3 | 1.35+ | AWS S3 |
| redis | 5.2+ | Caching |
| pytest | 8.3+ | Testing |
| black | 24.10+ | Formatting |
| ruff | 0.8+ | Linting |

---

## 🎯 Quick Start After Installation

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env with your settings
nano .env  # or use any editor

# 3. Create database
# (Make sure MySQL is running)

# 4. Run migrations
alembic upgrade head

# 5. Start the server
uvicorn app.main:app --reload

# 6. Access API documentation
# http://localhost:8000/docs
```

---

## 💡 Pro Tips

### Use pip-tools for reproducible builds:
```bash
pip install pip-tools
pip-compile requirements.txt
pip-sync requirements.txt
```

### Speed up installation:
```bash
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir --prefer-binary
```

### Use pre-compiled wheels:
```bash
pip install --only-binary :all: cryptography bcrypt psutil
```

### Check for outdated packages:
```bash
pip list --outdated
```

### Update all packages (be careful in production):
```bash
pip install --upgrade -r requirements.txt
```

---

## 🆘 Still Having Issues?

### Get Help:

1. **Check Python version**: Must be 3.10+
2. **Update pip**: `pip install --upgrade pip`
3. **Clear cache**: `pip cache purge`
4. **Try Docker**: Easiest method, no dependencies
5. **Install minimal**: Use `requirements-minimal.txt`
6. **Manual install**: Install packages one by one

### Common Solutions:

**All platforms:**
```bash
pip install --upgrade pip setuptools wheel
pip cache purge
pip install -r requirements.txt --no-cache-dir
```

**Linux specific:**
```bash
sudo apt-get install python3-dev build-essential libssl-dev libffi-dev
```

**macOS specific:**
```bash
xcode-select --install
brew install openssl
```

**Windows specific:**
```bash
# Install Visual C++ Build Tools first
# Then: pip install --only-binary :all: cryptography bcrypt
```

---

## ✅ Installation Complete!

Once installed, you should have:
- ✅ Python 3.10+ with virtual environment
- ✅ All 40+ packages installed
- ✅ FastAPI ready to run
- ✅ Database tools (SQLAlchemy, Alembic)
- ✅ AI integrations (OpenAI, Anthropic)
- ✅ Payment system (Stripe)
- ✅ File storage (Boto3/S3)

**Next steps:**
1. Configure `.env` file
2. Set up MySQL database
3. Run migrations: `alembic upgrade head`
4. Start server: `uvicorn app.main:app --reload`
5. Visit http://localhost:8000/docs

🎉 **Ready to build amazing things!**
