import boto3
from datetime import datetime
from typing import List, Dict, Optional
import os
import uuid
import urllib3

# Disable SSL warnings (temporary fix for SSL cert issues)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class KnowledgeBaseDB:
    """DynamoDB knowledge base for client-specific information"""
    
    def __init__(self):
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name=os.getenv('AWS_REGION', 'us-east-1'),
            verify=False  # Disable SSL verification temporarily
        )
        self.table_name = 'vantix-knowledge-base'
        self.table = None
        self._ensure_table()
    
    def _ensure_table(self):
        """Create table if it doesn't exist"""
        try:
            self.table = self.dynamodb.Table(self.table_name)
            self.table.load()
            print(f"✅ Connected to DynamoDB table: {self.table_name}")
        except self.dynamodb.meta.client.exceptions.ResourceNotFoundException:
            print(f"⚠️  Table {self.table_name} not found. Creating...")
            self._create_table()
    
    def _create_table(self):
        """Create the knowledge base table"""
        try:
            table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {'AttributeName': 'client_id', 'KeyType': 'HASH'},  # Partition key
                    {'AttributeName': 'knowledge_id', 'KeyType': 'RANGE'}  # Sort key
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'client_id', 'AttributeType': 'S'},
                    {'AttributeName': 'knowledge_id', 'AttributeType': 'S'},
                    {'AttributeName': 'category', 'AttributeType': 'S'}
                ],
                GlobalSecondaryIndexes=[
                    {
                        'IndexName': 'category-index',
                        'KeySchema': [
                            {'AttributeName': 'client_id', 'KeyType': 'HASH'},
                            {'AttributeName': 'category', 'KeyType': 'RANGE'}
                        ],
                        'Projection': {'ProjectionType': 'ALL'},
                        'ProvisionedThroughput': {
                            'ReadCapacityUnits': 5,
                            'WriteCapacityUnits': 5
                        }
                    }
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            
            # Wait for table to be created
            table.meta.client.get_waiter('table_exists').wait(TableName=self.table_name)
            self.table = table
            print(f"✅ Created DynamoDB table: {self.table_name}")
            
            # Add default knowledge for demo client
            self._seed_demo_data()
            
        except Exception as e:
            print(f"❌ Error creating table: {e}")
            # If table exists but we couldn't load it, try again
            self.table = self.dynamodb.Table(self.table_name)
    
    def _seed_demo_data(self):
        """Add default knowledge for demo client"""
        demo_knowledge = [
            {
                "category": "services",
                "title": "Emergency Plumbing",
                "content": "24/7 emergency service. We can be there in 2 hours. Handles burst pipes, major leaks, sewer backups.",
                "tags": ["emergency", "24/7", "urgent"]
            },
            {
                "category": "services",
                "title": "Drain Cleaning",
                "content": "Professional drain cleaning for kitchen sinks, bathroom sinks, tubs, and main lines. Most clogs cleared in under an hour. Uses hydro-jetting for tough clogs.",
                "tags": ["drain", "clog", "sink", "cleaning"]
            },
            {
                "category": "services",
                "title": "Water Heater Service",
                "content": "Water heater installation, repair, and maintenance. Same-day installation available. Works with tank and tankless models. 10-year warranty on new installations.",
                "tags": ["water heater", "hot water", "installation"]
            },
            {
                "category": "pricing",
                "title": "Standard Rates",
                "content": "Service call: $50 (waived if booked today). Hourly rate: $99/hour. Most jobs: $150-300. Emergency rate: $150/hour.",
                "tags": ["pricing", "cost", "rates"]
            },
            {
                "category": "pricing",
                "title": "Special Offers",
                "content": "Book today and save $50 on service call. Senior discount: 10% off. New customer special: Free drain inspection with any service.",
                "tags": ["discount", "special", "offer"]
            },
            {
                "category": "company",
                "title": "About Us",
                "content": "Joe's Plumbing - 20+ years serving the community. Licensed and insured. A+ BBB rating. Family-owned and operated. Satisfaction guaranteed.",
                "tags": ["about", "company", "experience"]
            },
            {
                "category": "availability",
                "title": "Current Availability",
                "content": "Today: 2PM-4PM (last slot). Tomorrow: 9AM-11AM, 2PM-4PM. Emergency service available 24/7.",
                "tags": ["booking", "schedule", "availability"]
            },
            {
                "category": "faqs",
                "title": "Payment Methods",
                "content": "We accept cash, credit cards (Visa, Mastercard, Amex), checks, and financing available for jobs over $500.",
                "tags": ["payment", "financing"]
            }
        ]
        
        for item in demo_knowledge:
            self.add_knowledge("demo_client", item)
    
    def add_knowledge(self, client_id: str, knowledge: Dict) -> str:
        """Add knowledge item for a client"""
        knowledge_id = str(uuid.uuid4())
        
        item = {
            'client_id': client_id,
            'knowledge_id': knowledge_id,
            'category': knowledge.get('category', 'general'),
            'title': knowledge.get('title', ''),
            'content': knowledge.get('content', ''),
            'tags': knowledge.get('tags', []),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        self.table.put_item(Item=item)
        print(f"✅ Added knowledge: {knowledge.get('title')} for {client_id}")
        return knowledge_id
    
    def get_all_knowledge(self, client_id: str) -> List[Dict]:
        """Get all knowledge for a client"""
        try:
            response = self.table.query(
                KeyConditionExpression='client_id = :client_id',
                ExpressionAttributeValues={':client_id': client_id}
            )
            return response.get('Items', [])
        except Exception as e:
            print(f"❌ Error getting knowledge: {e}")
            return []
    
    def get_knowledge_by_category(self, client_id: str, category: str) -> List[Dict]:
        """Get knowledge by category"""
        try:
            response = self.table.query(
                IndexName='category-index',
                KeyConditionExpression='client_id = :client_id AND category = :category',
                ExpressionAttributeValues={
                    ':client_id': client_id,
                    ':category': category
                }
            )
            return response.get('Items', [])
        except Exception as e:
            print(f"❌ Error getting knowledge by category: {e}")
            return []
    
    def search_knowledge(self, client_id: str, query: str) -> List[Dict]:
        """Search knowledge by tags or content (simple search)"""
        all_knowledge = self.get_all_knowledge(client_id)
        query_lower = query.lower()
        
        results = []
        for item in all_knowledge:
            # Search in title, content, and tags
            if (query_lower in item.get('title', '').lower() or
                query_lower in item.get('content', '').lower() or
                any(query_lower in tag.lower() for tag in item.get('tags', []))):
                results.append(item)
        
        return results
    
    def format_knowledge_for_ai(self, knowledge_items: List[Dict]) -> str:
        """Format knowledge items for AI context"""
        if not knowledge_items:
            return ""
        
        formatted = []
        for item in knowledge_items:
            formatted.append(f"**{item.get('title', 'Info')}**")
            formatted.append(item.get('content', ''))
            formatted.append("")  # Empty line
        
        return "\n".join(formatted)
    
    def update_knowledge(self, client_id: str, knowledge_id: str, updates: Dict):
        """Update a knowledge item"""
        updates['updated_at'] = datetime.now().isoformat()
        
        update_expression = "SET " + ", ".join([f"{k} = :{k}" for k in updates.keys()])
        expression_values = {f":{k}": v for k, v in updates.items()}
        
        self.table.update_item(
            Key={'client_id': client_id, 'knowledge_id': knowledge_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values
        )
    
    def delete_knowledge(self, client_id: str, knowledge_id: str):
        """Delete a knowledge item"""
        self.table.delete_item(
            Key={'client_id': client_id, 'knowledge_id': knowledge_id}
        )

class BotSettingsDB:
    """DynamoDB storage for bot personality and settings"""
    
    def __init__(self):
        self.dynamodb = boto3.resource(
            'dynamodb',
            region_name=os.getenv('AWS_REGION', 'us-east-1'),
            verify=False  # Disable SSL verification temporarily
        )
        self.table_name = 'vantix-bot-settings'
        self.table = None
        self._ensure_table()
    
    def _ensure_table(self):
        """Create table if it doesn't exist"""
        try:
            self.table = self.dynamodb.Table(self.table_name)
            self.table.load()
            print(f"✅ Connected to bot settings table: {self.table_name}")
        except self.dynamodb.meta.client.exceptions.ResourceNotFoundException:
            print(f"⚠️  Table {self.table_name} not found. Creating...")
            self._create_table()
    
    def _create_table(self):
        """Create the bot settings table"""
        try:
            table = self.dynamodb.create_table(
                TableName=self.table_name,
                KeySchema=[
                    {'AttributeName': 'client_id', 'KeyType': 'HASH'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'client_id', 'AttributeType': 'S'}
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 5,
                    'WriteCapacityUnits': 5
                }
            )
            
            table.meta.client.get_waiter('table_exists').wait(TableName=self.table_name)
            self.table = table
            print(f"✅ Created bot settings table: {self.table_name}")
            
        except Exception as e:
            print(f"❌ Error creating settings table: {e}")
            self.table = self.dynamodb.Table(self.table_name)
    
    def get_settings(self, client_id: str) -> Dict:
        """Get bot settings for a client"""
        try:
            response = self.table.get_item(Key={'client_id': client_id})
            if 'Item' in response:
                return response['Item']
            else:
                # Return default settings
                return self._get_default_settings(client_id)
        except Exception as e:
            print(f"❌ Error getting settings: {e}")
            return self._get_default_settings(client_id)
    
    def _get_default_settings(self, client_id: str) -> Dict:
        """Default bot settings"""
        return {
            'client_id': client_id,
            'personality': 'sales_focused',
            'tone': 'professional',
            'response_length': 'medium',
            'creativity': 0.7,
            'use_emojis': False,
            'formality_level': 7,
            'urgency_level': 8,
            'enable_quick_replies': True,
            'max_response_sentences': 3,
            'voice_enabled': False,
            'voice_id': 'default',
            'voice_speed': 1.0,
            'custom_instructions': '',
            'greeting_message': 'Hi! Need help? We can assist you today.',
            'updated_at': datetime.now().isoformat()
        }
    
    def update_settings(self, client_id: str, settings: Dict):
        """Update bot settings"""
        settings['client_id'] = client_id
        settings['updated_at'] = datetime.now().isoformat()
        
        self.table.put_item(Item=settings)
        print(f"✅ Updated settings for {client_id}")
    
    def get_system_prompt(self, client_id: str, base_prompt: str) -> str:
        """Generate system prompt based on settings"""
        settings = self.get_settings(client_id)
        
        # Personality templates
        personalities = {
            'professional': "You are a professional, courteous assistant. Be formal and precise.",
            'friendly': "You are a warm, friendly assistant. Be conversational and approachable.",
            'sales_focused': "You are a sales-focused assistant. Create urgency and guide toward booking.",
            'technical': "You are a technical expert. Provide detailed, accurate information.",
            'casual': "You are a casual, laid-back assistant. Keep it simple and relatable."
        }
        
        # Tone modifiers
        tones = {
            'formal': "Use formal language. Avoid contractions and slang.",
            'professional': "Use professional business language.",
            'conversational': "Use natural, conversational language.",
            'casual': "Use casual, everyday language."
        }
        
        # Response length
        lengths = {
            'brief': f"Keep responses to 1-2 sentences maximum.",
            'medium': f"Keep responses to {settings.get('max_response_sentences', 3)} sentences maximum.",
            'detailed': "Provide comprehensive responses with full details."
        }
        
        # Build custom prompt
        custom_prompt = f"""
{personalities.get(settings.get('personality', 'sales_focused'), personalities['sales_focused'])}

TONE: {tones.get(settings.get('tone', 'professional'), tones['professional'])}

RESPONSE LENGTH: {lengths.get(settings.get('response_length', 'medium'), lengths['medium'])}

FORMALITY LEVEL: {settings.get('formality_level', 7)}/10 (10 = most formal)
URGENCY LEVEL: {settings.get('urgency_level', 8)}/10 (10 = highest urgency)

EMOJIS: {'Use emojis sparingly to add warmth' if settings.get('use_emojis') else 'Do not use emojis'}

QUICK REPLIES: {'When appropriate, suggest 2-3 quick reply options in JSON format' if settings.get('enable_quick_replies') else 'Do not suggest quick replies'}

{f"CUSTOM INSTRUCTIONS: {settings.get('custom_instructions')}" if settings.get('custom_instructions') else ''}

{base_prompt}
"""
        
        return custom_prompt
