import boto3
from botocore.exceptions import ClientError
from typing import Optional, Dict, List, Any
from datetime import datetime
import uuid
import os
import logging

logger = logging.getLogger(__name__)

class DynamoDBClient:
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_REGION', 'ap-southeast-1'))
        self.table_name = os.getenv('DYNAMODB_TABLE_NAME', 'WellArchitectedApp')
        self.table = self.dynamodb.Table(self.table_name)
    
    def put_item(self, item: Dict) -> bool:
        """Insert or update an item"""
        try:
            self.table.put_item(Item=item)
            return True
        except ClientError as e:
            logger.error(f"Error putting item: {e}")
            return False
    
    def get_item(self, pk: str, sk: str) -> Optional[Dict]:
        """Get an item by primary key"""
        try:
            response = self.table.get_item(Key={'PK': pk, 'SK': sk})
            return response.get('Item')
        except ClientError as e:
            logger.error(f"Error getting item: {e}")
            return None
    
    def query_by_pk(self, pk: str, sk_prefix: Optional[str] = None) -> List[Dict]:
        """Query items by partition key"""
        try:
            if sk_prefix:
                response = self.table.query(
                    KeyConditionExpression='PK = :pk AND begins_with(SK, :sk)',
                    ExpressionAttributeValues={':pk': pk, ':sk': sk_prefix}
                )
            else:
                response = self.table.query(
                    KeyConditionExpression='PK = :pk',
                    ExpressionAttributeValues={':pk': pk}
                )
            return response.get('Items', [])
        except ClientError as e:
            logger.error(f"Error querying items: {e}")
            return []
    
    def query_gsi(self, gsi_name: str, gsi_pk: str, gsi_sk: Optional[str] = None) -> List[Dict]:
        """Query items using GSI"""
        try:
            if gsi_sk:
                response = self.table.query(
                    IndexName=gsi_name,
                    KeyConditionExpression='GSI1PK = :pk AND GSI1SK = :sk',
                    ExpressionAttributeValues={':pk': gsi_pk, ':sk': gsi_sk}
                )
            else:
                response = self.table.query(
                    IndexName=gsi_name,
                    KeyConditionExpression='GSI1PK = :pk',
                    ExpressionAttributeValues={':pk': gsi_pk}
                )
            return response.get('Items', [])
        except ClientError as e:
            logger.error(f"Error querying GSI: {e}")
            return []
    
    def update_item(self, pk: str, sk: str, updates: Dict) -> bool:
        """Update specific attributes of an item"""
        try:
            update_expression = "SET " + ", ".join([f"#{k} = :{k}" for k in updates.keys()])
            expression_attribute_names = {f"#{k}": k for k in updates.keys()}
            expression_attribute_values = {f":{k}": v for k, v in updates.items()}
            
            self.table.update_item(
                Key={'PK': pk, 'SK': sk},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values
            )
            return True
        except ClientError as e:
            logger.error(f"Error updating item: {e}")
            return False
    
    def delete_item(self, pk: str, sk: str) -> bool:
        """Delete an item"""
        try:
            self.table.delete_item(Key={'PK': pk, 'SK': sk})
            return True
        except ClientError as e:
            logger.error(f"Error deleting item: {e}")
            return False

# Singleton instance
db_client = DynamoDBClient()
