from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import boto3
import json
import os
from datetime import datetime
from dotenv import load_dotenv
from database import KnowledgeBaseDB, BotSettingsDB
from scraper import WebScraper
from document_processor import DocumentProcessor
from auth import ClientAuth

load_dotenv()

app = FastAPI(title="Vantix Voice Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize knowledge base, scraper, document processor, and bot settings
try:
    knowledge_db = KnowledgeBaseDB()
    print("✅ Knowledge base initialized")
except Exception as e:
    print(f"⚠️  Knowledge base initialization failed: {e}")
    knowledge_db = None

try:
    bot_settings_db = BotSettingsDB()
    print("✅ Bot settings initialized")
except Exception as e:
    print(f"⚠️  Bot settings initialization failed: {e}")
    bot_settings_db = None

try:
    client_auth = ClientAuth()
    print("✅ Client auth initialized")
except Exception as e:
    print(f"⚠️  Client auth initialization failed: {e}")
    client_auth = None

scraper = WebScraper()
doc_processor = DocumentProcessor()

try:
    bedrock = boto3.client(
        service_name='bedrock-runtime',
        region_name=os.getenv('AWS_REGION', 'us-east-1')
    )
    print("✅ Bedrock client initialized successfully")
except Exception as e:
    print(f"❌ Failed to initialize Bedrock client: {e}")
    bedrock = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    client_id: str
    user_id: str
    message: str
    conversation_history: Optional[List[ChatMessage]] = []

class QuickReply(BaseModel):
    text: str
    value: str

class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    quick_replies: Optional[List[QuickReply]] = []

class KnowledgeItem(BaseModel):
    category: str
    title: str
    content: str
    tags: Optional[List[str]] = []

conversations = {}
client_configs = {
    "demo_client": {
        "business_name": "Joe's Plumbing",
        "logo_url": "https://via.placeholder.com/40x40/007bff/ffffff?text=JP",
        "system_prompt": """You are a sales-focused AI assistant for Joe's Plumbing. Your PRIMARY GOAL is to book appointments and convert leads.

PERSONALITY:
- Confident and solution-oriented
- Create urgency without being pushy
- Empathetic to customer problems
- Always guide toward booking
- Professional but warm

SALES STRATEGY:
1. Acknowledge the problem with empathy
2. Position yourself as the solution
3. Create urgency (availability, problem worsening)
4. Offer immediate booking with time slots
5. Overcome objections smoothly
6. Always ask for the sale

RESPONSE FORMAT - IMPORTANT:
Keep responses to 2-3 sentences maximum. Be conversational and natural.

When offering options, provide them as quick reply buttons by adding a JSON block AFTER your message:

Example response:
"Hey there! What plumbing issue can I help you with today?"

```json
{
  "quick_replies": [
    {"text": "I have a leak", "value": "leak"},
    {"text": "Clogged drain", "value": "drain"},
    {"text": "Water heater issue", "value": "water_heater"}
  ]
}
```

CRITICAL: The JSON block should be SEPARATE from your message, wrapped in ```json code block.

BOOKING FLOW:
1. Problem identification → Empathize + position as solution
2. Offer immediate time slots (create urgency)
3. Collect contact info
4. Confirm and upsell if appropriate

OBJECTION HANDLING:
- Price concerns: Emphasize value, emergency costs, problem worsening
- "Just looking": Offer free quote, limited availability
- Timing: "We have a slot opening up today/tomorrow"

URGENCY TRIGGERS:
- "We have limited availability this week"
- "This type of issue can worsen quickly"
- "We can get someone out today"
- "Special rate if we book now"

Always guide the conversation toward booking. Every response should move closer to a scheduled appointment.""",
        "knowledge_base": """
        Joe's Plumbing Services:
        - Emergency Plumbing (24/7) - "We can be there in 2 hours"
        - Drain Cleaning - "Most clogs cleared in under an hour"
        - Water Heater Service - "Same-day installation available"
        - Leak Detection - "Prevent costly water damage"
        - Pipe Repair - "Stop leaks before they get worse"
        
        Pricing (Use to overcome objections):
        - Service call: $50 (waived if you book today)
        - Standard rate: $99/hour
        - Emergency rate: $150/hour
        - Average job: $150-300
        
        Value Props:
        - Licensed & insured
        - 20+ years experience
        - Same-day service available
        - Free estimates
        - Satisfaction guaranteed
        
        Hours: Mon-Fri 8AM-6PM, Emergency 24/7
        Phone: (555) 123-4567
        
        Available slots (create urgency):
        - Today 2PM-4PM (Last slot!)
        - Tomorrow 9AM-11AM
        - Tomorrow 2PM-4PM
        - Custom time
        
        SALES TIPS:
        - Clogged drains can cause backups and flooding
        - Leaks waste water and increase bills
        - Water heater issues mean no hot water
        - Emergency calls cost more - book regular hours
        """
    }
}

def call_claude(messages: List[dict], system_prompt: str) -> str:
    if bedrock is None:
        return "Error: Bedrock client not initialized. Please check your AWS credentials."
    
    try:
        formatted_messages = []
        for msg in messages:
            formatted_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "system": system_prompt,
            "messages": formatted_messages,
            "temperature": 0.7
        }
        
        print(f"🤖 Calling Claude with {len(formatted_messages)} messages...")
        
        response = bedrock.invoke_model(
            modelId=os.getenv('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0'),
            body=json.dumps(request_body)
        )
        
        result = json.loads(response['body'].read())
        assistant_message = result['content'][0]['text']
        
        print(f"✅ Claude responded: {assistant_message[:100]}...")
        return assistant_message
    
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Bedrock error: {error_msg}")
        
        if "AccessDeniedException" in error_msg:
            return "Error: Please enable Claude 3.5 Sonnet in AWS Bedrock Model Access settings."
        elif "ValidationException" in error_msg:
            return "Error: Invalid request to Claude. Please check the configuration."
        else:
            return f"Error: {error_msg}"

@app.get("/")
def health_check():
    bedrock_status = "connected" if bedrock else "not initialized"
    return {
        "status": "healthy",
        "service": "Vantix Voice Agent",
        "python_version": "3.9.6",
        "bedrock_status": bedrock_status
    }

@app.get("/test-bedrock")
def test_bedrock():
    try:
        response = call_claude(
            messages=[{"role": "user", "content": "Say hello in one sentence"}],
            system_prompt="You are a helpful assistant."
        )
        return {"status": "success", "response": response}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    print(f"\n📨 Received chat request from client: {request.client_id}")
    
    if request.client_id not in client_configs:
        raise HTTPException(status_code=404, detail=f"Client '{request.client_id}' not found")
    
    config = client_configs[request.client_id]
    
    # Build conversation history
    messages = []
    for msg in request.conversation_history:
        messages.append({
            "role": msg.role,
            "content": msg.content
        })
    
    messages.append({
        "role": "user",
        "content": request.message
    })
    
    print(f"💬 User message: {request.message}")
    
    # Get relevant knowledge from DynamoDB
    knowledge_context = ""
    if knowledge_db:
        # Search for relevant knowledge based on user message
        relevant_knowledge = knowledge_db.search_knowledge(request.client_id, request.message)
        if relevant_knowledge:
            knowledge_context = "\n\nRELEVANT KNOWLEDGE:\n" + knowledge_db.format_knowledge_for_ai(relevant_knowledge)
            print(f"📚 Found {len(relevant_knowledge)} relevant knowledge items")
    
    # Build system prompt with knowledge and bot settings
    base_system_prompt = f"{config['system_prompt']}\n\nKNOWLEDGE BASE:\n{config['knowledge_base']}{knowledge_context}"
    
    # Apply bot settings to system prompt
    if bot_settings_db:
        system_prompt = bot_settings_db.get_system_prompt(request.client_id, base_system_prompt)
    else:
        system_prompt = base_system_prompt
    
    ai_response = call_claude(messages=messages, system_prompt=system_prompt)
    
    # Try to parse JSON response for quick replies
    quick_replies = []
    message_text = ai_response
    
    try:
        import re
        # Look for JSON block with quick_replies
        json_match = re.search(r'```json\s*(\{[\s\S]*?\})\s*```', ai_response)
        if json_match:
            # Extract JSON and parse it
            json_str = json_match.group(1)
            response_data = json.loads(json_str)
            
            # Remove the JSON block from the message
            message_text = re.sub(r'```json\s*\{[\s\S]*?\}\s*```', '', ai_response).strip()
            
            # Extract quick replies
            if "quick_replies" in response_data:
                quick_replies = response_data["quick_replies"]
            
            print(f"✅ Parsed {len(quick_replies)} quick replies")
        else:
            # Try without code block
            json_match = re.search(r'\{[\s\S]*"quick_replies"[\s\S]*?\}', ai_response)
            if json_match:
                response_data = json.loads(json_match.group())
                message_text = re.sub(r'\{[\s\S]*"quick_replies"[\s\S]*?\}', '', ai_response).strip()
                quick_replies = response_data.get("quick_replies", [])
                print(f"✅ Parsed {len(quick_replies)} quick replies (no code block)")
    except Exception as e:
        print(f"⚠️  Could not parse quick replies: {e}")
        # If parsing fails, just use the full response as message
        message_text = ai_response
        quick_replies = []
    
    conversation_id = f"{request.client_id}_{request.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    conversations[conversation_id] = {
        "client_id": request.client_id,
        "user_id": request.user_id,
        "messages": messages + [{"role": "assistant", "content": message_text}],
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"✅ Stored conversation: {conversation_id}")
    print(f"📊 Total conversations: {len(conversations)}\n")
    
    return ChatResponse(
        message=message_text,
        conversation_id=conversation_id,
        quick_replies=quick_replies
    )

@app.get("/config/{client_id}")
async def get_client_config(client_id: str):
    if client_id not in client_configs:
        raise HTTPException(status_code=404, detail=f"Client '{client_id}' not found")
    
    config = client_configs[client_id]
    
    return {
        "client_id": client_id,
        "business_name": config["business_name"],
        "logo_url": config.get("logo_url"),
        "widget_settings": {
            "primary_color": "#007bff",
            "position": "bottom-right",
            "greeting": f"Hi! Need a plumber? We can help today. What's going on?"
        }
    }

@app.get("/conversations")
async def list_conversations():
    return {
        "total": len(conversations),
        "conversations": list(conversations.keys())
    }

# Knowledge Base Endpoints
@app.post("/knowledge/{client_id}")
async def add_knowledge(client_id: str, knowledge: KnowledgeItem):
    """Add knowledge item for a client"""
    if not knowledge_db:
        raise HTTPException(status_code=503, detail="Knowledge base not available")
    
    knowledge_id = knowledge_db.add_knowledge(client_id, knowledge.dict())
    return {
        "success": True,
        "knowledge_id": knowledge_id,
        "message": f"Added knowledge: {knowledge.title}"
    }

@app.get("/knowledge/{client_id}")
async def get_knowledge(client_id: str, category: Optional[str] = None):
    """Get all knowledge or by category for a client"""
    if not knowledge_db:
        raise HTTPException(status_code=503, detail="Knowledge base not available")
    
    if category:
        items = knowledge_db.get_knowledge_by_category(client_id, category)
    else:
        items = knowledge_db.get_all_knowledge(client_id)
    
    return {
        "client_id": client_id,
        "count": len(items),
        "knowledge": items
    }

@app.get("/knowledge/{client_id}/search")
async def search_knowledge(client_id: str, q: str):
    """Search knowledge base"""
    if not knowledge_db:
        raise HTTPException(status_code=503, detail="Knowledge base not available")
    
    results = knowledge_db.search_knowledge(client_id, q)
    return {
        "query": q,
        "count": len(results),
        "results": results
    }

@app.delete("/knowledge/{client_id}/{knowledge_id}")
async def delete_knowledge(client_id: str, knowledge_id: str):
    """Delete a knowledge item"""
    if not knowledge_db:
        raise HTTPException(status_code=503, detail="Knowledge base not available")
    
    knowledge_db.delete_knowledge(client_id, knowledge_id)
    return {"success": True, "message": "Knowledge deleted"}

# Bot Settings Endpoints
@app.get("/settings/{client_id}")
async def get_bot_settings(client_id: str):
    """Get bot personality and behavior settings"""
    if not bot_settings_db:
        raise HTTPException(status_code=503, detail="Settings not available")
    
    settings = bot_settings_db.get_settings(client_id)
    return settings

@app.put("/settings/{client_id}")
async def update_bot_settings(client_id: str, settings: dict):
    """Update bot settings"""
    if not bot_settings_db:
        raise HTTPException(status_code=503, detail="Settings not available")
    
    bot_settings_db.update_settings(client_id, settings)
    return {"success": True, "message": "Settings updated"}

@app.post("/scrape/{client_id}")
async def scrape_website(client_id: str, url: str):
    """Scrape a website and add to knowledge base"""
    if not knowledge_db:
        raise HTTPException(status_code=503, detail="Knowledge base not available")
    
    print(f"🕷️  Scraping website for {client_id}: {url}")
    
    try:
        # Scrape the website
        scraped_data = scraper.scrape_website(url)
        
        # Format for knowledge base
        knowledge_items = scraper.format_for_knowledge_base(scraped_data, client_id)
        
        # Add to knowledge base
        added_count = 0
        for item in knowledge_items:
            knowledge_db.add_knowledge(client_id, item)
            added_count += 1
        
        return {
            "success": True,
            "url": url,
            "items_added": added_count,
            "summary": {
                "services": len(scraped_data["services"]),
                "faqs": len(scraped_data["faqs"]),
                "pricing": len(scraped_data["pricing"])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@app.post("/upload/{client_id}")
async def upload_document(client_id: str, file: UploadFile = File(...)):
    """Upload and process a document"""
    if not knowledge_db:
        raise HTTPException(status_code=503, detail="Knowledge base not available")
    
    print(f"📄 Processing upload for {client_id}: {file.filename}")
    
    try:
        # Read file content
        content = await file.read()
        
        # Process document
        processed = doc_processor.process_file(content, file.filename)
        
        # Chunk the text
        chunks = doc_processor.chunk_text(processed['full_text'])
        
        # Add each chunk to knowledge base
        added_count = 0
        for i, chunk in enumerate(chunks):
            # Auto-categorize
            category = doc_processor.auto_categorize(chunk)
            
            # Extract key points for title
            key_points = doc_processor.extract_key_points(chunk, max_points=1)
            title = key_points[0] if key_points else f"{file.filename} - Part {i+1}"
            
            knowledge_db.add_knowledge(client_id, {
                "category": category,
                "title": title[:100],  # Limit title length
                "content": chunk,
                "tags": [processed['type'], file.filename, category],
                "source": file.filename,
                "chunk_index": i
            })
            added_count += 1
        
        return {
            "success": True,
            "filename": file.filename,
            "type": processed['type'],
            "chunks_added": added_count,
            "categories_detected": list(set([doc_processor.auto_categorize(c) for c in chunks]))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

# Authentication Endpoints
class LoginRequest(BaseModel):
    client_id: str
    password: str

class TokenVerifyRequest(BaseModel):
    client_id: str
    access_token: str

@app.post("/auth/login")
async def login(request: LoginRequest):
    """Client login - returns access token"""
    if not client_auth:
        raise HTTPException(status_code=503, detail="Auth not available")
    
    access_token = client_auth.verify_password(request.client_id, request.password)
    
    if not access_token:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return {
        "success": True,
        "access_token": access_token,
        "client_id": request.client_id
    }

@app.post("/auth/verify")
async def verify_token(request: TokenVerifyRequest):
    """Verify access token"""
    if not client_auth:
        raise HTTPException(status_code=503, detail="Auth not available")
    
    is_valid = client_auth.verify_token(request.client_id, request.access_token)
    
    return {"valid": is_valid}

@app.post("/voice/webhook")
async def voice_webhook(request: dict):
    """Handle incoming Twilio voice calls"""
    from twilio.twiml.voice_response import VoiceResponse
    
    print(f"\n📞 Incoming call from: {request.get('From')}")
    
    response = VoiceResponse()
    response.say("Hello! Thank you for calling. Our AI assistant will be with you shortly.")
    
    # TODO: Connect to LiveKit room
    # For now, just gather speech
    response.gather(
        input='speech',
        action='/voice/process',
        speechTimeout='auto'
    )
    
    return {"twiml": str(response)}

@app.post("/voice/process")
async def voice_process(request: dict):
    """Process speech input from call"""
    speech_result = request.get('SpeechResult', '')
    
    print(f"🎤 Speech received: {speech_result}")
    
    # Get AI response
    ai_response = call_claude(
        messages=[{"role": "user", "content": speech_result}],
        system_prompt="You are a helpful phone assistant. Keep responses brief and conversational."
    )
    
    from twilio.twiml.voice_response import VoiceResponse
    response = VoiceResponse()
    response.say(ai_response)
    response.gather(
        input='speech',
        action='/voice/process',
        speechTimeout='auto'
    )
    
    return {"twiml": str(response)}

@app.post("/voice/outbound")
async def initiate_outbound_call(to_number: str, client_id: str):
    """Initiate an outbound call"""
    # TODO: Implement with Twilio
    return {"status": "not_implemented"}

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Starting Vantix Voice Agent Backend...")
    print(f"🐍 Python version: 3.9.6")
    print(f"🌍 Region: {os.getenv('AWS_REGION', 'us-east-1')}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
