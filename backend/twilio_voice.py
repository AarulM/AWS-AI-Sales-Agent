"""
Twilio Voice Handler with AWS Bedrock + Polly
Simple phone-based voice agent
"""

import os
import json
import boto3
from fastapi import APIRouter, Request, Response
from twilio.twiml.voice_response import VoiceResponse, Gather
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# AWS clients
bedrock = boto3.client('bedrock-runtime', region_name=os.getenv('AWS_REGION', 'us-east-1'))
polly = boto3.client('polly', region_name=os.getenv('AWS_REGION', 'us-east-1'))

# Store conversations in memory (use Redis/DynamoDB in production)
conversations = {}

SYSTEM_PROMPT = """You are a friendly AI assistant for Joe's Plumbing. 

Keep responses VERY brief (1-2 sentences max). This is a phone call.

Services: Emergency Plumbing 24/7, Drain Cleaning, Water Heater Service, Leak Detection.

If they want to book, collect: Name, Phone, Address, Best time.

Available slots: Today 2PM-4PM, Tomorrow 9AM-11AM, Tomorrow 2PM-4PM."""


def get_ai_response(call_sid: str, user_text: str) -> str:
    """Get response from AWS Bedrock"""
    
    # Get or create conversation
    if call_sid not in conversations:
        conversations[call_sid] = []
    
    conversations[call_sid].append({"role": "user", "content": user_text})
    
    try:
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 150,
            "system": SYSTEM_PROMPT,
            "messages": conversations[call_sid][-10:],  # Last 10 messages
            "temperature": 0.7
        }
        
        response = bedrock.invoke_model(
            modelId=os.getenv('BEDROCK_MODEL_ID', 'us.anthropic.claude-sonnet-4-6'),
            body=json.dumps(request_body)
        )
        
        result = json.loads(response['body'].read())
        ai_text = result['content'][0]['text']
        
        conversations[call_sid].append({"role": "assistant", "content": ai_text})
        
        print(f"👤 User: {user_text}")
        print(f"🤖 AI: {ai_text}")
        
        return ai_text
    
    except Exception as e:
        print(f"❌ Bedrock error: {e}")
        return "I'm having trouble processing that. Could you repeat?"


def synthesize_speech(text: str) -> str:
    """Generate speech URL using AWS Polly"""
    try:
        response = polly.synthesize_speech(
            Text=text,
            OutputFormat='mp3',
            VoiceId='Joanna',
            Engine='neural'
        )
        
        # In production, save to S3 and return URL
        # For now, we'll use Twilio's <Say> with SSML
        return text
    
    except Exception as e:
        print(f"❌ Polly error: {e}")
        return text


@router.post("/voice/incoming")
async def handle_incoming_call(request: Request):
    """Handle incoming Twilio call"""
    
    form_data = await request.form()
    call_sid = form_data.get('CallSid')
    from_number = form_data.get('From')
    
    print(f"📞 Incoming call from {from_number}")
    
    response = VoiceResponse()
    
    # Greeting
    greeting = "Hey there! Thanks for calling Joe's Plumbing. What can I help you with today?"
    response.say(greeting, voice='Polly.Joanna')
    
    # Gather speech input
    gather = Gather(
        input='speech',
        action='/voice/process',
        speech_timeout='auto',
        language='en-US'
    )
    response.append(gather)
    
    # If no input, repeat
    response.say("I didn't catch that. What can I help you with?", voice='Polly.Joanna')
    response.redirect('/voice/incoming')
    
    return Response(content=str(response), media_type="application/xml")


@router.post("/voice/process")
async def process_speech(request: Request):
    """Process speech input and respond"""
    
    form_data = await request.form()
    call_sid = form_data.get('CallSid')
    speech_result = form_data.get('SpeechResult', '')
    
    if not speech_result:
        response = VoiceResponse()
        response.say("I didn't hear anything. Could you repeat that?", voice='Polly.Joanna')
        response.redirect('/voice/incoming')
        return Response(content=str(response), media_type="application/xml")
    
    # Get AI response
    ai_response = get_ai_response(call_sid, speech_result)
    
    # Create TwiML response
    response = VoiceResponse()
    response.say(ai_response, voice='Polly.Joanna')
    
    # Continue conversation
    gather = Gather(
        input='speech',
        action='/voice/process',
        speech_timeout='auto',
        language='en-US'
    )
    response.append(gather)
    
    # If no more input, end call
    response.say("Thanks for calling Joe's Plumbing! Have a great day!", voice='Polly.Joanna')
    response.hangup()
    
    return Response(content=str(response), media_type="application/xml")


@router.post("/voice/status")
async def call_status(request: Request):
    """Handle call status updates"""
    
    form_data = await request.form()
    call_sid = form_data.get('CallSid')
    call_status = form_data.get('CallStatus')
    
    print(f"📊 Call {call_sid}: {call_status}")
    
    # Clean up conversation when call ends
    if call_status in ['completed', 'failed', 'busy', 'no-answer']:
        if call_sid in conversations:
            del conversations[call_sid]
    
    return {"status": "ok"}
