import json
import os
import boto3
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
table_name = os.environ.get('DYNAMODB_TABLE', 'FinancialTracker')
table = dynamodb.Table(table_name)

def lambda_handler(event, context):
    print("Received event:", json.dumps(event))
    http_method = event.get('requestContext', {}).get('http', {}).get('method', '')
    
    try:
        if http_method == 'OPTIONS':
            return build_response(200, "CORS Preflight OK")
        elif http_method == 'POST':
            return create_transaction(event)
        elif http_method == 'GET':
            return get_transactions(event)
        elif http_method == 'DELETE':
            return delete_transaction(event)
        elif http_method == 'PUT':
            return update_transaction_note(event)
        else:
            return build_response(400, {"error": f"Unsupported HTTP method: {http_method}"})
            
    except Exception as e:
        print("Error:", str(e))
        return build_response(500, {"error": "Internal server error", "details": str(e)})

def create_transaction(event):
    body = json.loads(event.get('body', '{}'))
    user_id = "USER#123"
    
    amount = body.get('amount')
    category = body.get('category', 'Uncategorized')
    txn_type = body.get('type', 'expense')
    note = body.get('note', '')
    
    if not amount:
        return build_response(400, {"error": "Amount is required"})
        
    date_str = datetime.utcnow().strftime('%Y-%m-%d')
    txn_id = str(uuid.uuid4())[:8]
    sort_key = f"TXN#{date_str}#{txn_id}"
    
    item = {
        'PK': user_id,
        'SK': sort_key,
        'amount': str(amount),
        'category': category,
        'type': txn_type,
        'note': note,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    table.put_item(Item=item)
    
    numeric_amount = Decimal(str(amount))
    delta = numeric_amount if txn_type == 'income' else -numeric_amount
    
    table.update_item(
        Key={'PK': user_id, 'SK': 'BALANCE'},
        UpdateExpression="ADD current_balance :delta",
        ExpressionAttributeValues={':delta': delta}
    )
    
    return build_response(201, {"message": "Transaction created", "transaction": item})

def update_transaction_note(event):
    """Updates only the note field of a specific transaction"""
    body = json.loads(event.get('body', '{}'))
    user_id = "USER#123"
    sk = body.get('sk')
    note = body.get('note', '')
    
    if not sk:
        return build_response(400, {"error": "Transaction SK is required"})
        
    table.update_item(
        Key={'PK': user_id, 'SK': sk},
        UpdateExpression="SET note = :note",
        ExpressionAttributeValues={':note': note}
    )
    
    return build_response(200, {"message": "Note updated successfully"})

def delete_transaction(event):
    body = json.loads(event.get('body', '{}'))
    user_id = "USER#123"
    sk_to_delete = body.get('sk')
    
    if not sk_to_delete:
        return build_response(400, {"error": "Transaction SK is required"})
        
    response = table.get_item(Key={'PK': user_id, 'SK': sk_to_delete})
    txn = response.get('Item')
    
    if not txn:
        return build_response(404, {"error": "Transaction not found"})
        
    amount = Decimal(str(txn.get('amount', '0')))
    txn_type = txn.get('type', 'expense')
    
    table.delete_item(Key={'PK': user_id, 'SK': sk_to_delete})
    
    reverse_delta = amount if txn_type == 'expense' else -amount
    table.update_item(
        Key={'PK': user_id, 'SK': 'BALANCE'},
        UpdateExpression="ADD current_balance :delta",
        ExpressionAttributeValues={':delta': reverse_delta}
    )
    
    return build_response(200, {"message": "Transaction deleted"})

def get_transactions(event):
    user_id = "USER#123"
    query_params = event.get('queryStringParameters') or {}
    
    month_filter = query_params.get('month')
    time_range = query_params.get('range')
    
    if month_filter:
        sk_condition = "PK = :pk AND begins_with(SK, :sk_val)"
        sk_val = f"TXN#{month_filter}"
    elif time_range and time_range != 'all':
        now = datetime.utcnow()
        if time_range == '3m':
            start_date = now - timedelta(days=90)
        elif time_range == '6m':
            start_date = now - timedelta(days=180)
        elif time_range == '1y':
            start_date = now - timedelta(days=365)
        else:
            start_date = now - timedelta(days=180)
            
        sk_condition = "PK = :pk AND SK >= :sk_val"
        sk_val = f"TXN#{start_date.strftime('%Y-%m-%d')}"
    else:
        sk_condition = "PK = :pk AND begins_with(SK, :sk_val)"
        sk_val = "TXN#"
        
    txn_response = table.query(
        KeyConditionExpression=sk_condition,
        ExpressionAttributeValues={":pk": user_id, ":sk_val": sk_val}
    )
    
    balance_response = table.get_item(Key={'PK': user_id, 'SK': 'BALANCE'})
    current_balance = balance_response.get('Item', {}).get('current_balance', Decimal('0'))
    
    return build_response(200, {
        "balance": int(current_balance),
        "transactions": txn_response.get('Items', [])
    })

def build_response(status_code, body):
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