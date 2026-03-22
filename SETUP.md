# Setup Instructions

## Prerequisites
- Python 3.9+
- Node.js 18+
- AWS Account with Bedrock access

## Step 1: Configure AWS

```bash
aws configure
# Enter: Access Key, Secret Key, Region (us-east-1)
```

Enable Claude 3.5 Sonnet in AWS Bedrock Console.

## Step 2: Backend Setup

```bash
cd vantix-voice-agent/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp ../.env.example .env
# Edit .env with your AWS credentials

# Start server
python main.py
```

Backend runs on: `http://localhost:8000`

## Step 3: Frontend Setup

```bash
cd vantix-voice-agent/frontend/widget

# Install dependencies
npm install

# Start dev server
npm run dev
```

Frontend runs on: `http://localhost:5174`

## Step 4: Test

1. Open: `http://localhost:5174?demo=true`
2. Click "Client Login"
3. Enter password: `admin123`
4. Click "Login"
5. Settings button (⚙️) should appear above chat button

## Troubleshooting

### Settings Button Not Showing

**Check browser console (F12) for:**
```
🔑 Access token: [token]
🔍 Verifying auth with token: [token]
✅ Auth verified: true
🎯 isAuthenticated changed to: true
```

**If you see errors:**
1. Clear localStorage: `localStorage.clear()`
2. Refresh page
3. Login again

**If still not working:**
```bash
# Test auth endpoint directly
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"client_id": "demo_client", "password": "admin123"}'
```

Should return:
```json
{
  "success": true,
  "access_token": "...",
  "client_id": "demo_client"
}
```

### Backend Not Starting

```bash
# Check if port 8000 is in use
lsof -ti:8000

# Kill process if needed
kill -9 $(lsof -ti:8000)

# Restart backend
python main.py
```

### Frontend Not Starting

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
npm run dev
```

## Next Steps

1. Customize bot personality in Settings Panel
2. Upload documents or scrape website for knowledge base
3. Test chat functionality
4. Build for production: `npm run build`
5. Deploy to your hosting provider

## Support

Check `README.md` for full documentation and API reference.
