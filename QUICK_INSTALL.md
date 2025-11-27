# ⚡ Quick Installation Reference

## 🚀 Fastest Method (Docker)

```bash
docker-compose up --build
```
✅ No Python setup needed!

---

## 🐍 Standard Python Installation

### 1. Create Environment
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 2. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**If errors occur:**
```bash
pip install -r requirements-minimal.txt
```

---

## 🔧 Fix Common Errors

### Error: "python-email-validator not found"
```bash
pip install email-validator>=2.2.0
```

### Error: "cryptography build failed"
```bash
# Linux:
sudo apt-get install build-essential libssl-dev python3-dev

# Mac:
brew install openssl

# Windows:
pip install --only-binary :all: cryptography
```

### Error: "bcrypt build failed"
```bash
# Linux:
sudo apt-get install build-essential python3-dev

# Mac:
xcode-select --install

# Windows:
pip install --only-binary :all: bcrypt
```

---

## ✅ Verify Installation

```bash
python -c "import fastapi; print('✅ FastAPI OK')"
python -c "import sqlalchemy; print('✅ SQLAlchemy OK')"
python -c "import pydantic; print('✅ Pydantic OK')"
python -c "from app.main import app; print('✅ App OK')"
```

---

## 📦 Latest Package Versions (Nov 2024)

- FastAPI: 0.115+
- Uvicorn: 0.32+
- SQLAlchemy: 2.0.36+
- Pydantic: 2.10+
- OpenAI: 1.57+
- Anthropic: 0.40+
- Stripe: 11.2+
- Boto3: 1.35+

---

## 🎯 Start the Server

```bash
# 1. Setup environment
cp .env.example .env

# 2. Run migrations
alembic upgrade head

# 3. Start server
uvicorn app.main:app --reload

# 4. Open browser
# http://localhost:8000/docs
```

---

## 💡 Pro Tips

### Speed up installation:
```bash
pip install -r requirements.txt --prefer-binary --no-cache-dir
```

### Clear issues:
```bash
pip cache purge
pip install --upgrade pip setuptools wheel
```

### Install one by one:
```bash
pip install fastapi uvicorn sqlalchemy pymysql pydantic python-dotenv
pip install python-jose passlib authlib httpx stripe boto3 openai
```

---

## 📚 Full Guides

- **Complete Installation**: See `INSTALLATION_GUIDE.md`
- **Quick Start**: See `QUICKSTART.md`
- **Full Setup**: See `README.md`

---

## 🆘 Need Help?

1. ✅ Use Docker (easiest)
2. ✅ Use Python 3.11 or 3.12
3. ✅ Update pip: `pip install --upgrade pip`
4. ✅ Clear cache: `pip cache purge`
5. ✅ Try minimal: `requirements-minimal.txt`

---

**Python Version Required**: 3.10+ (3.11 or 3.12 recommended)

**Check version**: `python --version`
