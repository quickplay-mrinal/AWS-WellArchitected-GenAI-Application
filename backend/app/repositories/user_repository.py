from typing import Optional, Dict
from datetime import datetime
import uuid
from app.db.dynamodb import db_client

class UserRepository:
    @staticmethod
    def create_user(email: str, username: str, hashed_password: str, full_name: Optional[str] = None) -> Dict:
        user_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        user_item = {
            'PK': f'USER#{user_id}',
            'SK': 'PROFILE',
            'GSI1PK': f'EMAIL#{email}',
            'GSI1SK': f'USER#{user_id}',
            'user_id': user_id,
            'email': email,
            'username': username,
            'hashed_password': hashed_password,
            'full_name': full_name or '',
            'is_active': True,
            'created_at': timestamp,
            'updated_at': timestamp,
        }
        
        db_client.put_item(user_item)
        return user_item
    
    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[Dict]:
        return db_client.get_item(f'USER#{user_id}', 'PROFILE')
    
    @staticmethod
    def get_user_by_email(email: str) -> Optional[Dict]:
        items = db_client.query_gsi('GSI1', f'EMAIL#{email}')
        return items[0] if items else None
    
    @staticmethod
    def get_user_by_username(username: str) -> Optional[Dict]:
        # Use scan with filter for username lookup
        # Note: For production, consider adding a GSI on username for better performance
        try:
            response = db_client.table.scan(
                FilterExpression='username = :username',
                ExpressionAttributeValues={':username': username}
            )
            items = response.get('Items', [])
            return items[0] if items else None
        except Exception as e:
            from app.db.dynamodb import logger
            logger.error(f"Error getting user by username: {e}")
            return None
    
    @staticmethod
    def update_user(user_id: str, updates: Dict) -> bool:
        updates['updated_at'] = datetime.utcnow().isoformat()
        return db_client.update_item(f'USER#{user_id}', 'PROFILE', updates)
