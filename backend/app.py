import json
import os
import boto3
import uuid
from datetime import datetime
from decimal import Decimal

# Initialize the DynamoDB client
dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('DYNAMODB_TABLE', 'FinancialTracker')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    print("Received event:", json.dumps(event))
    
    http_method = event.get('requestContext', {}).get('http', {}).get('method', '')
    
    try:
        # 1. Handle the CORS Preflight request
        if http_method == 'OPTIONS':
            return build_response(200, "CORS Preflight OK")
            
        # 2. Handle actual requests
        elif http_method == 'POST':
            return create_transaction(event)
        elif http_method == 'GET':
            return get_transactions(event)
        else:
            return build_response(400, {"error": f"Unsupported HTTP method: {http_method}"})
            
    except Exception as e:
        print("Error:", str(e))
        return build_response(500, {"error": "Internal server error", "details": str(e)})

def create_transaction(event):
    """Parses JSON, saves transaction, and updates the running balance atomically"""
    body = json.loads(event.get('body', '{}'))
    
    user_id = "USER#123"
    amount = body.get('amount')
    category = body.get('category', 'Uncategorized')
    txn_type = body.get('type', 'expense')
    
    if not amount:
        return build_response(400, {"error": "Amount is required"})
        
    # 1. Generate Transaction Item
    date_str = datetime.utcnow().strftime('%Y-%m-%d')
    txn_id = str(uuid.uuid4())[:8]
    sort_key = f"TXN#{date_str}#{txn_id}"
    
    item = {
        'PK': user_id,
        'SK': sort_key,
        'amount': str(amount),
        'category': category,
        'type': txn_type,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # 2. Write the transaction
    table.put_item(Item=item)
    
    # 3. Update the Running Balance using an Atomic Counter
    # Convert amount to Decimal for DynamoDB math. Negative for expenses.
    numeric_amount = Decimal(str(amount))
    delta = numeric_amount if txn_type == 'income' else -numeric_amount
    
    table.update_item(
        Key={
            'PK': user_id,
            'SK': 'BALANCE'
        },
        UpdateExpression="ADD current_balance :delta",
        ExpressionAttributeValues={
            ':delta': delta
        }
    )
    
    return build_response(201, {"message": "Transaction created and balance updated", "transaction": item})

def get_transactions(event):
    """Fetches transactions, filtered by month if provided"""
    user_id = "USER#123"
    
    # Check for query parameters (e.g., ?month=2026-10)
    query_params = event.get('queryStringParameters') or {}
    month_filter = query_params.get('month')
    
    # If a month is provided, query only that month. Otherwise, fetch all TXNs.
    sk_prefix = f"TXN#{month_filter}" if month_filter else "TXN#"
    
    # Fetch the transactions
    txn_response = table.query(
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_prefix)",
        ExpressionAttributeValues={
            ":pk": user_id,
            ":sk_prefix": sk_prefix
        }
    )
    
    # Fetch the running balance
    balance_response = table.get_item(
        Key={
            'PK': user_id,
            'SK': 'BALANCE'
        }
    )
    
    # Safely extract the balance (defaults to 0 if the user has no transactions yet)
    current_balance = balance_response.get('Item', {}).get('current_balance', Decimal('0'))
    
    return build_response(200, {
        "balance": int(current_balance),
        "transactions": txn_response.get('Items', [])
    })

def build_response(status_code, body):
    """Helper function to format the response for API Gateway"""
    # Convert any stray Decimals to int/float for JSON serialization
    class DecimalEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, Decimal):
                return float(obj) if obj % 1 else int(obj)
            return super(DecimalEncoder, self).default(obj)

    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body, cls=DecimalEncoder)
    }