from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import boto3
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Vantix Voice Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

class ChatResponse(BaseModel):
    message: str
    conversation_id: str

conversations = {}
client_configs = {
    "demo_client": {
        "business_name": "Joe's Plumbing",
        "system_prompt": "You are a helpful assistant for Joe's Plumbing. Help customers schedule appointments and answer questions about our services. Be friendly and professional.",
        "knowledge_base": """
        Joe's Plumbing Services:
        - 24/7 Emergency Plumbing
        - Drain Cleaning & Repair
        - Water Heater Installation & Repair
        - Leak Detection
        - Pipe Repair & Replacement
        
        Pricing:
        - Service call fee: $50
        - Hourly rate: $99/hour
        - Emergency rate (after hours): $150/hour
        
        Hours: Monday-Friday 8AM-6PM, Emergency service 24/7
        Phone: (555) 123-4567
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
    
    system_prompt = f"{config['system_prompt']}\n\nKnowledge Base:\n{config['knowledge_base']}"
    ai_response = call_claude(messages=messages, system_prompt=system_prompt)
    
    conversation_id = f"{request.client_id}_{request.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    conversations[conversation_id] = {
        "client_id": request.client_id,
        "user_id": request.user_id,
        "messages": messages + [{"role": "assistant", "content": ai_response}],
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"✅ Stored conversation: {conversation_id}")
    print(f"📊 Total conversations: {len(conversations)}\n")
    
    return ChatResponse(
        message=ai_response,
        conversation_id=conversation_id
    )

@app.get("/config/{client_id}")
async def get_client_config(client_id: str):
    if client_id not in client_configs:
        raise HTTPException(status_code=404, detail=f"Client '{client_id}' not found")
    
    return {
        "client_id": client_id,
        "business_name": client_configs[client_id]["business_name"],
        "widget_settings": {
            "primary_color": "#007bff",
            "position": "bottom-right",
            "greeting": f"Hi! How can {client_configs[client_id]['business_name']} help you today?"
        }
    }

@app.get("/conversations")
async def list_conversations():
    return {
        "total": len(conversations),
        "conversations": list(conversations.keys())
    }

if __name__ == "__main__":
    import uvicorn
    print("\n🚀 Starting Vantix Voice Agent Backend...")
    print(f"🐍 Python version: 3.9.6")
    print(f"🌍 Region: {os.getenv('AWS_REGION', 'us-east-1')}")
    uvicorn.run(app, host="0.0.0.0", port=8000)
