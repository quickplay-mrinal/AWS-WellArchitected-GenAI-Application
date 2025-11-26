# This file is not used - the application uses DynamoDB instead of SQL
# Kept for potential future SQL database integration
# The DynamoDB client is in app/db/dynamodb.py

from app.db.dynamodb import db_client

def get_db():
    """Returns the DynamoDB client instance"""
    return db_client
