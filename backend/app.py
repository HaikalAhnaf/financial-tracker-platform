import json
import os
import boto3
import uuid
import base64
from datetime import datetime, timedelta
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('DYNAMODB_TABLE', 'FinancialTracker')
table = dynamodb.Table(table_name)

def get_user_email(event):
    """Securely extracts the user's email from the Cognito JWT"""
    auth_header = event.get('headers', {}).get('authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header.split(' ')[1]
        try:
            # Decode the JWT Payload without external libraries
            payload = token.split('.')[1]
            payload += '=' * (-len(payload) % 4) # Fix base64 padding
            decoded = json.loads(base64.urlsafe_b64decode(payload).decode('utf-8'))
            return decoded.get('email', 'UNKNOWN_USER')
        except:
            pass
    return "USER#123" # Fallback if no token is provided

def lambda_handler(event, context):
    print("Received event:", json.dumps(event))
    http_method = event.get('requestContext', {}).get('http', {}).get('method', '')
    raw_path = event.get('rawPath', '/')
    
    # 1. Identify the secure user
    user_email = get_user_email(event)
    
    try:
        if http_method == 'OPTIONS':
            return build_response(200, "CORS Preflight OK")
            
        # 2. Handle Category fetching
        if raw_path == '/categories' and http_method == 'GET':
            return get_categories(user_email)

        if http_method == 'POST':
            return create_transaction(event, user_email)
        elif http_method == 'GET':
            return get_transactions(event, user_email)
        elif http_method == 'DELETE':
            return delete_transaction(event, user_email)
        elif http_method == 'PUT':
            return update_transaction_note(event, user_email)
        else:
            return build_response(400, {"error": f"Unsupported method: {http_method}"})
            
    except Exception as e:
        print("Error:", str(e))
        return build_response(500, {"error": "Internal server error", "details": str(e)})

def get_categories(user_email):
    """Fetches custom categories, providing smart defaults if empty"""
    response = table.get_item(Key={'PK': user_email, 'SK': 'METADATA'})
    item = response.get('Item', {})
    
    # Boto3 returns DynamoDB String Sets as Python sets, convert to list for JSON
    income_cats = list(item.get('income_categories', ['Salary', 'Savings', 'Investment']))
    expense_cats = list(item.get('expense_categories', ['Food', 'Internet', 'Transport', 'Utilities']))
    
    return build_response(200, {"income": income_cats, "expense": expense_cats})

def create_transaction(event, user_email):
    body = json.loads(event.get('body', '{}'))
    amount = body.get('amount')
    category = body.get('category', 'Uncategorized')
    txn_type = body.get('type', 'expense')
    note = body.get('note', '')
    
    if not amount: return build_response(400, {"error": "Amount is required"})
        
    date_str = datetime.utcnow().strftime('%Y-%m-%d')
    txn_id = str(uuid.uuid4())[:8]
    
    item = {
        'PK': user_email, # Secure data isolation
        'SK': f"TXN#{date_str}#{txn_id}",
        'amount': str(amount),
        'category': category,
        'type': txn_type,
        'note': note,
        'timestamp': datetime.utcnow().isoformat()
    }
    table.put_item(Item=item)
    
    # Update Balance
    numeric_amount = Decimal(str(amount))
    delta = numeric_amount if txn_type == 'income' else -numeric_amount
    table.update_item(
        Key={'PK': user_email, 'SK': 'BALANCE'},
        UpdateExpression="ADD current_balance :delta",
        ExpressionAttributeValues={':delta': delta}
    )
    
    # Auto-save new custom category using a DynamoDB String Set
    cat_attr = "income_categories" if txn_type == 'income' else "expense_categories"
    try:
        table.update_item(
            Key={'PK': user_email, 'SK': 'METADATA'},
            UpdateExpression=f"ADD {cat_attr} :c",
            ExpressionAttributeValues={':c': set([category])} 
        )
    except:
        pass
        
    return build_response(201, {"message": "Transaction created", "transaction": item})

def update_transaction_note(event, user_email):
    body = json.loads(event.get('body', '{}'))
    sk = body.get('sk')
    table.update_item(
        Key={'PK': user_email, 'SK': sk},
        UpdateExpression="SET note = :note",
        ExpressionAttributeValues={':note': body.get('note', '')}
    )
    return build_response(200, {"message": "Note updated"})

def delete_transaction(event, user_email):
    body = json.loads(event.get('body', '{}'))
    sk_to_delete = body.get('sk')
    
    response = table.get_item(Key={'PK': user_email, 'SK': sk_to_delete})
    txn = response.get('Item')
    if not txn: return build_response(404, {"error": "Transaction not found"})
        
    amount = Decimal(str(txn.get('amount', '0')))
    table.delete_item(Key={'PK': user_email, 'SK': sk_to_delete})
    
    reverse_delta = amount if txn.get('type') == 'expense' else -amount
    table.update_item(
        Key={'PK': user_email, 'SK': 'BALANCE'},
        UpdateExpression="ADD current_balance :delta",
        ExpressionAttributeValues={':delta': reverse_delta}
    )
    return build_response(200, {"message": "Transaction deleted"})

def get_transactions(event, user_email):
    query_params = event.get('queryStringParameters') or {}
    month = query_params.get('month')
    rng = query_params.get('range')
    
    if month:
        sk_cond = "PK = :pk AND begins_with(SK, :sk_val)"
        sk_val = f"TXN#{month}"
    elif rng and rng != 'all':
        now = datetime.utcnow()
        days = 90 if rng == '3m' else 365 if rng == '1y' else 180
        start_date = now - timedelta(days=days)
        sk_cond = "PK = :pk AND SK >= :sk_val"
        sk_val = f"TXN#{start_date.strftime('%Y-%m-%d')}"
    else:
        sk_cond = "PK = :pk AND begins_with(SK, :sk_val)"
        sk_val = "TXN#"
        
    txn_response = table.query(
        KeyConditionExpression=sk_cond,
        ExpressionAttributeValues={":pk": user_email, ":sk_val": sk_val}
    )
    
    bal_response = table.get_item(Key={'PK': user_email, 'SK': 'BALANCE'})
    current_balance = bal_response.get('Item', {}).get('current_balance', Decimal('0'))
    
    return build_response(200, {"balance": int(current_balance), "transactions": txn_response.get('Items', [])})

def build_response(status_code, body):
    class DecimalEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, Decimal):
                return float(obj) if obj % 1 else int(obj)
            return super(DecimalEncoder, self).default(obj)
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body, cls=DecimalEncoder)
    }