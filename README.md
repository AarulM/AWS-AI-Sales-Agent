# Vantix AI Voice + Chat Agent

Modern AI-powered chat widget for service businesses. Built with React, FastAPI, and AWS Bedrock (Claude 3.5 Sonnet).

## Quick Start

### 1. Start Backend
```bash
cd vantix-voice-agent/backend
source venv/bin/activate
python main.py
```

### 2. Start Frontend
```bash
cd vantix-voice-agent/frontend/widget
npm install
npm run dev
```

### 3. Open Browser
Visit: `http://localhost:5174?demo=true`

Login with password: `admin123`

## Features

- 💬 Real-time AI chat with Claude 3.5 Sonnet
- 📚 Knowledge base (upload docs, scrape websites)
- 🎭 Customizable bot personality
- ⚙️ Settings panel (client-only access)
- 📏 Resizable widget (3 sizes)
- 🎨 Modern UI with smooth animations
- 🔐 Client authentication system

## Project Structure

```
vantix-voice-agent/
├── backend/
│   ├── main.py              # FastAPI server
│   ├── database.py          # DynamoDB operations
│   ├── auth.py              # Client authentication
│   ├── scraper.py           # Website scraping
│   ├── document_processor.py # Document upload
│   └── requirements.txt
│
├── frontend/widget/
│   ├── src/
│   │   ├── App.jsx          # Demo page
│   │   ├── ChatWidget-new.jsx    # Main widget
│   │   ├── ChatWidget-new.css    # Widget styles
│   │   ├── SettingsPanel.jsx     # Settings UI
│   │   └── SettingsPanel.css
│   └── package.json
│
└── README.md
```

## Configuration

### Backend (.env)
```bash
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
BEDROCK_MODEL_ID=anthropic.claude-3-5-sonnet-20241022-v2:0
```

### Create Client Account
```python
from auth import ClientAuth
auth = ClientAuth()
auth.create_client("client_id", "password", "Business Name")
```

## API Endpoints

### Chat
```bash
POST /chat
{
  "client_id": "demo_client",
  "user_id": "user_123",
  "message": "Hello",
  "conversation_history": []
}
```

### Authentication
```bash
POST /auth/login
{
  "client_id": "demo_client",
  "password": "admin123"
}
```

### Knowledge Base
```bash
POST /knowledge/{client_id}
GET /knowledge/{client_id}
DELETE /knowledge/{client_id}/{knowledge_id}
```

### Bot Settings
```bash
GET /settings/{client_id}
PUT /settings/{client_id}
```

## Usage

### Customer View (Public)
```
http://localhost:5174
```
- Only chat button visible
- No authentication required
- This is what customers see

### Client View (Admin)
```
http://localhost:5174?demo=true
```
- Login section visible
- After login: Settings + Resize buttons appear
- For testing/configuration

## Deployment

### Build Frontend
```bash
cd frontend/widget
npm run build
```

### Deploy Backend
- AWS Lambda + API Gateway
- AWS Fargate
- Any cloud provider

### Embed Widget
```html
<script src="https://your-cdn.com/widget.js"></script>
<script>
  VantixWidget.init({
    clientId: 'CLIENT_ID',
    apiUrl: 'https://your-api.com'
  });
</script>
```

## Troubleshooting

### Settings Button Not Showing
1. Visit `?demo=true` URL
2. Login with password
3. Check browser console for auth logs
4. Verify backend is running

### Chat Not Responding
1. Check backend logs
2. Verify AWS Bedrock access
3. Test: `curl http://localhost:8000/test-bedrock`

### Input Text Not Visible
Fixed! Text is now dark gray on light background.

## Tech Stack

- **Frontend**: React 19, Vite, Framer Motion, Axios
- **Backend**: FastAPI, Python 3.9
- **AI**: AWS Bedrock (Claude 3.5 Sonnet)
- **Database**: DynamoDB
- **Fonts**: Inter, Poppins

## License

MIT
