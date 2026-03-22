import boto3
import hashlib
import secrets
from datetime import datetime
from typing import Optional, Dict
import os

class ClientAuth:
    """Authentication system for client access to settings"""
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'us-east-1'))
        self.table_name = 'vantix-client-auth'
        self.table = None
        self._ensure_table()
    
    def _ensure_table(self):
        """Create table if it doesn't exist"""
        try:
            self.table = self.dynamodb.Table(self.table_name)
            self.table.load()
            print(f"✅ Connected to auth table: {self.table_name}")
        except self.dynamodb.meta.client.exceptions.ResourceNotFoundException:
            print(f"⚠️  Table {self.table_name} not found. Creating...")
            self._create_table()
    
    def _create_table(self):
        """Create the client auth table"""
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
            print(f"✅ Created auth table: {self.table_name}")
            
            # Create demo client credentials
            self._create_demo_client()
            
        except Exception as e:
            print(f"❌ Error creating auth table: {e}")
            self.table = self.dynamodb.Table(self.table_name)
    
    def _create_demo_client(self):
        """Create demo client with default credentials"""
        # Default password: "admin123"
        self.create_client("demo_client", "admin123", "Joe's Plumbing")
    
    def create_client(self, client_id: str, password: str, business_name: str) -> Dict:
        """Create a new client with credentials"""
        # Generate access token
        access_token = secrets.token_urlsafe(32)
        
        # Hash password
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        item = {
            'client_id': client_id,
            'password_hash': password_hash,
            'access_token': access_token,
            'business_name': business_name,
            'created_at': datetime.now().isoformat(),
            'last_login': None
        }
        
        self.table.put_item(Item=item)
        print(f"✅ Created client: {client_id}")
        
        return {
            'client_id': client_id,
            'access_token': access_token,
            'business_name': business_name
        }
    
    def verify_password(self, client_id: str, password: str) -> Optional[str]:
        """Verify password and return access token if valid"""
        try:
            response = self.table.get_item(Key={'client_id': client_id})
            
            if 'Item' not in response:
                return None
            
            item = response['Item']
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            if item['password_hash'] == password_hash:
                # Update last login
                self.table.update_item(
                    Key={'client_id': client_id},
                    UpdateExpression='SET last_login = :login',
                    ExpressionAttributeValues={':login': datetime.now().isoformat()}
                )
                return item['access_token']
            
            return None
            
        except Exception as e:
            print(f"❌ Error verifying password: {e}")
            return None
    
    def verify_token(self, client_id: str, access_token: str) -> bool:
        """Verify access token"""
        try:
            response = self.table.get_item(Key={'client_id': client_id})
            
            if 'Item' not in response:
                return False
            
            return response['Item']['access_token'] == access_token
            
        except Exception as e:
            print(f"❌ Error verifying token: {e}")
            return False
    
    def regenerate_token(self, client_id: str) -> Optional[str]:
        """Generate new access token"""
        try:
            new_token = secrets.token_urlsafe(32)
            
            self.table.update_item(
                Key={'client_id': client_id},
                UpdateExpression='SET access_token = :token',
                ExpressionAttributeValues={':token': new_token}
            )
            
            return new_token
            
        except Exception as e:
            print(f"❌ Error regenerating token: {e}")
            return None
    
    def change_password(self, client_id: str, old_password: str, new_password: str) -> bool:
        """Change client password"""
        # Verify old password first
        if not self.verify_password(client_id, old_password):
            return False
        
        try:
            new_hash = hashlib.sha256(new_password.encode()).hexdigest()
            
            self.table.update_item(
                Key={'client_id': client_id},
                UpdateExpression='SET password_hash = :hash',
                ExpressionAttributeValues={':hash': new_hash}
            )
            
            return True
            
        except Exception as e:
            print(f"❌ Error changing password: {e}")
            return False
