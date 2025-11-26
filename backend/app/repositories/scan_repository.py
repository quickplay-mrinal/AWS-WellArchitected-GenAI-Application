from typing import Optional, Dict, List
from datetime import datetime
import uuid
from app.db.dynamodb import db_client

class ScanRepository:
    @staticmethod
    def create_scan(user_id: str, credential_id: str, scan_name: str) -> Dict:
        scan_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        scan_item = {
            'PK': f'USER#{user_id}',
            'SK': f'SCAN#{scan_id}',
            'GSI1PK': f'SCAN#{scan_id}',
            'GSI1SK': f'TIMESTAMP#{timestamp}',
            'scan_id': scan_id,
            'user_id': user_id,
            'credential_id': credential_id,
            'scan_name': scan_name,
            'status': 'pending',
            'progress': 0,
            'regions_scanned': [],
            'results': {},
            'ai_recommendations': '',
            'error_message': '',
            'created_at': timestamp,
            'updated_at': timestamp,
        }
        
        db_client.put_item(scan_item)
        return scan_item
    
    @staticmethod
    def get_scan_by_id(scan_id: str) -> Optional[Dict]:
        items = db_client.query_gsi('GSI1', f'SCAN#{scan_id}')
        return items[0] if items else None
    
    @staticmethod
    def get_user_scans(user_id: str) -> List[Dict]:
        return db_client.query_by_pk(f'USER#{user_id}', 'SCAN#')
    
    @staticmethod
    def update_scan(user_id: str, scan_id: str, updates: Dict) -> bool:
        updates['updated_at'] = datetime.utcnow().isoformat()
        return db_client.update_item(f'USER#{user_id}', f'SCAN#{scan_id}', updates)
    
    @staticmethod
    def delete_scan(user_id: str, scan_id: str) -> bool:
        return db_client.delete_item(f'USER#{user_id}', f'SCAN#{scan_id}')
