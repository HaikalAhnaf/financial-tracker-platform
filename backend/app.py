import json
import os
import boto3
import uuid
from datetime import datetime

# Initialize the DynamoDB client
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('DYNAMODB_TABLE', 'FinancialTracker')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    print("Received event:", json.dumps(event))
    
    http_method = event.get('requestContext', {}).get('http', {}).get('method', '')
    
    try:
        # 1. Handle the CORS Preflight request from the browser
        if http_method == 'OPTIONS':
            return build_response(200, "CORS Preflight OK")
            
        # 2. Handle the actual data requests
        elif http_method == 'POST':
            return create_transaction(event)
        elif http_method == 'GET':
            return get_transactions()
        else:
            return build_response(400, {"error": f"Unsupported HTTP method: {http_method}"})
            
    except Exception as e:
        print("Error:", str(e))
        return build_response(500, {"error": "Internal server error", "details": str(e)})

def create_transaction(event):
    """Parses JSON from the user and saves a new transaction to DynamoDB"""
    body = json.loads(event.get('body', '{}'))
    
    # We will hardcode a test user ID for now until we add Cognito Auth
    user_id = "USER#123"
    
    amount = body.get('amount')
    category = body.get('category', 'Uncategorized')
    txn_type = body.get('type', 'expense') # income or expense
    
    if not amount:
        return build_response(400, {"error": "Amount is required"})
        
    # Generate unique Sort Key: TXN#2026-10-16#<random-uuid>
    date_str = datetime.utcnow().strftime('%Y-%m-%d')
    txn_id = str(uuid.uuid4())[:8]
    sort_key = f"TXN#{date_str}#{txn_id}"
    
    item = {
        'PK': user_id,
        'SK': sort_key,
        'amount': str(amount), # DynamoDB prefers numbers as strings or Decimals
        'category': category,
        'type': txn_type,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    table.put_item(Item=item)
    return build_response(201, {"message": "Transaction created successfully", "transaction": item})

def get_transactions():
    """Fetches all transactions for our test user"""
    user_id = "USER#123"
    
    # Query DynamoDB for items where PK is the user AND SK starts with 'TXN#'
    response = table.query(
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
        ExpressionAttributeValues={
            ":pk": user_id,
            ":sk_prefix": "TXN#"
        }
    )
    
    return build_response(200, {"transactions": response.get('Items', [])})

def build_response(status_code, body):
    """Helper function to format the response for API Gateway"""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body)
    }