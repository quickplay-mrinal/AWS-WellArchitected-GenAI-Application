from typing import Optional, Dict, List
from datetime import datetime
import uuid
from app.db.dynamodb import db_client

class CredentialRepository:
    @staticmethod
    def create_credential(user_id: str, credential_name: str, encrypted_access_key: str, encrypted_secret_key: str) -> Dict:
        cred_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        cred_item = {
            'PK': f'USER#{user_id}',
            'SK': f'CRED#{cred_id}',
            'GSI1PK': f'CRED#{cred_id}',
            'GSI1SK': f'USER#{user_id}',
            'credential_id': cred_id,
            'user_id': user_id,
            'credential_name': credential_name,
            'encrypted_access_key': encrypted_access_key,
            'encrypted_secret_key': encrypted_secret_key,
            'is_active': True,
            'created_at': timestamp,
            'updated_at': timestamp,
        }
        
        db_client.put_item(cred_item)
        return cred_item
    
    @staticmethod
    def get_credential_by_id(cred_id: str) -> Optional[Dict]:
        items = db_client.query_gsi('GSI1', f'CRED#{cred_id}')
        return items[0] if items else None
    
    @staticmethod
    def get_user_credentials(user_id: str) -> List[Dict]:
        return db_client.query_by_pk(f'USER#{user_id}', 'CRED#')
    
    @staticmethod
    def update_credential(user_id: str, cred_id: str, updates: Dict) -> bool:
        updates['updated_at'] = datetime.utcnow().isoformat()
        return db_client.update_item(f'USER#{user_id}', f'CRED#{cred_id}', updates)
    
    @staticmethod
    def delete_credential(user_id: str, cred_id: str) -> bool:
        return db_client.delete_item(f'USER#{user_id}', f'CRED#{cred_id}')
