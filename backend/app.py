import json
import os
import boto3
import uuid
import base64
from datetime import datetime, timedelta
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses', region_name=os.environ.get('AWS_REGION', 'ap-southeast-1'))
table_name = os.environ.get('DYNAMODB_TABLE', 'FinancialTracker')
table = dynamodb.Table(table_name)

def extract_user_id(event):
    headers = {k.lower(): v for k, v in event.get('headers', {}).items()}
    auth_header = headers.get('authorization', '')
    if not auth_header.startswith('Bearer '): raise ValueError("Missing Auth header")
    token = auth_header.split(' ')[1]
    payload_part = token.split('.')[1]
    payload_part += '=' * ((4 - len(payload_part) % 4) % 4)
    decoded = json.loads(base64.urlsafe_b64decode(payload_part).decode('utf-8'))
    email = decoded.get('email')
    if not email: raise ValueError("Invalid token")
    return f"USER#{email}", email

def lambda_handler(event, context):
    print("Received event:", json.dumps(event))
    
    # Check if triggered automatically by EventBridge
    if event.get('source') == 'aws.events':
        return process_automated_reports()

    http_method = event.get('requestContext', {}).get('http', {}).get('method', '')
    
    try:
        if http_method == 'OPTIONS':
            return build_response(200, "CORS Preflight OK")
            
        user_id, user_email = extract_user_id(event)
        query_params = event.get('queryStringParameters') or {}
        entity = query_params.get('entity')
        
        if entity == 'settings':
            if http_method == 'GET': return get_settings(user_id)
            if http_method == 'POST': return save_settings(event, user_id)
        elif entity == 'report' and http_method == 'POST':
            return generate_and_send_report(user_id, user_email)
        elif entity == 'category':
            if http_method == 'POST': return create_category(event, user_id)
            if http_method == 'GET': return get_categories(user_id)
            if http_method == 'DELETE': return delete_category(event, user_id)
        else:
            if http_method == 'POST': return create_transaction(event, user_id)
            if http_method == 'GET': return get_transactions(event, user_id)
            if http_method == 'DELETE': return delete_transaction(event, user_id)
            if http_method == 'PUT': return update_transaction_note(event, user_id)
            
        return build_response(400, {"error": "Unsupported method/entity combination"})
            
    except ValueError as ve:
        return build_response(401, {"error": "Unauthorized", "details": str(ve)})
    except Exception as e:
        print("Error:", str(e))
        return build_response(500, {"error": "Internal server error", "details": str(e)})

# ==========================================
# REPORTING LOGIC
# ==========================================
def get_settings(user_id):
    response = table.get_item(Key={'PK': user_id, 'SK': 'SETTINGS'})
    settings = response.get('Item', {'reports_enabled': False, 'report_emails': []})
    return build_response(200, {"settings": settings})

def save_settings(event, user_id):
    body = json.loads(event.get('body', '{}'))
    item = {
        'PK': user_id,
        'SK': 'SETTINGS',
        'reports_enabled': body.get('reports_enabled', False),
        'report_emails': body.get('report_emails', [])
    }
    table.put_item(Item=item)
    return build_response(200, {"message": "Settings saved", "settings": item})

def process_automated_reports():
    """Scans for all users with reports enabled and sends them."""
    # Note: For massive scale, use a GSI, but scan is fine for portfolio
    response = table.scan(FilterExpression="SK = :sk AND reports_enabled = :true", ExpressionAttributeValues={":sk": "SETTINGS", ":true": True})
    for user_settings in response.get('Items', []):
        user_id = user_settings['PK']
        user_email = user_id.split('#')[1]
        generate_and_send_report(user_id, user_email, is_automated=True)
    return {"statusCode": 200, "body": "Automated reports processed"}

def generate_and_send_report(user_id, user_email, is_automated=False):
    response = table.get_item(Key={'PK': user_id, 'SK': 'SETTINGS'})
    settings = response.get('Item', {})
    emails_to_send = settings.get('report_emails', [user_email])
    
    if not emails_to_send:
        return build_response(400, {"error": "No email addresses configured."})

    # Fetch this month's transactions
    month_str = datetime.utcnow().strftime('%Y-%m')
    txn_response = table.query(
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_val)",
        ExpressionAttributeValues={":pk": user_id, ":sk_val": f"TXN#{month_str}"}
    )
    txns = txn_response.get('Items', [])
    
    income = sum([Decimal(t['amount']) for t in txns if t['type'] == 'income'])
    expense = sum([Decimal(t['amount']) for t in txns if t['type'] == 'expense'])
    net = income - expense
    
    subject = f"Your Financial Tracker Report - {month_str}"
    body_text = f"Monthly Report for {month_str}\n\nTotal Income: Rp {income}\nTotal Expenses: Rp {expense}\nNet Savings: Rp {net}\n\nTotal Transactions: {len(txns)}"
    
    try:
        # Dynamically use the verified user_email as the Source sender
        ses.send_email(
            Source=user_email,
            Destination={'ToAddresses': emails_to_send},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body_text}}
            }
        )
        return build_response(200, {"message": "Report sent successfully!"})
    except Exception as e:
        print("SES Error:", e)
        return build_response(500, {"error": "Failed to send email. Verify emails in AWS SES.", "details": str(e)})

# [Keep your existing create_transaction, update_transaction_note, delete_transaction, get_transactions, create_category, get_categories, delete_category, and build_response functions exactly as they were here]

# ==========================================
# TRANSACTION LOGIC
# ==========================================
def create_transaction(event, user_id):
    body = json.loads(event.get('body', '{}'))
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

def update_transaction_note(event, user_id):
    body = json.loads(event.get('body', '{}'))
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

def delete_transaction(event, user_id):
    body = json.loads(event.get('body', '{}'))
    sk_to_delete = body.get('sk')
    
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

def get_transactions(event, user_id):
    query_params = event.get('queryStringParameters') or {}
    month_filter = query_params.get('month')
    time_range = query_params.get('range')
    
    if month_filter:
        sk_condition = "PK = :pk AND begins_with(SK, :sk_val)"
        sk_val = f"TXN#{month_filter}"
    elif time_range and time_range != 'all':
        now = datetime.utcnow()
        if time_range == '3m': start_date = now - timedelta(days=90)
        elif time_range == '6m': start_date = now - timedelta(days=180)
        elif time_range == '1y': start_date = now - timedelta(days=365)
        else: start_date = now - timedelta(days=180)
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

# ==========================================
# CATEGORY LOGIC
# ==========================================
def create_category(event, user_id):
    body = json.loads(event.get('body', '{}'))
    name = body.get('name')
    cat_type = body.get('type') # 'income' or 'expense'
    
    if not name or not cat_type:
        return build_response(400, {"error": "Category name and type are required"})
        
    # SK format: CATEGORY#expense#food
    sort_key = f"CATEGORY#{cat_type}#{name.lower()}"
    
    item = {
        'PK': user_id,
        'SK': sort_key,
        'name': name,
        'type': cat_type,
        'timestamp': datetime.utcnow().isoformat()
    }
    table.put_item(Item=item)
    return build_response(201, {"message": "Category created", "category": item})

def get_categories(user_id):
    response = table.query(
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_val)",
        ExpressionAttributeValues={":pk": user_id, ":sk_val": "CATEGORY#"}
    )
    
    # Provide default categories if the user has none yet
    categories = response.get('Items', [])
    if not categories:
        defaults = [
            {'PK': user_id, 'SK': 'CATEGORY#expense#food', 'name': 'Food', 'type': 'expense'},
            {'PK': user_id, 'SK': 'CATEGORY#expense#transport', 'name': 'Transport', 'type': 'expense'},
            {'PK': user_id, 'SK': 'CATEGORY#income#salary', 'name': 'Salary', 'type': 'income'}
        ]
        for cat in defaults:
            table.put_item(Item=cat)
        categories = defaults

    return build_response(200, {"categories": categories})

def delete_category(event, user_id):
    body = json.loads(event.get('body', '{}'))
    sk_to_delete = body.get('sk')
    if not sk_to_delete:
        return build_response(400, {"error": "Category SK is required"})
        
    table.delete_item(Key={'PK': user_id, 'SK': sk_to_delete})
    return build_response(200, {"message": "Category deleted"})

def build_response(status_code, body):
    class DecimalEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, Decimal): return float(obj) if obj % 1 else int(obj)
            return super(DecimalEncoder, self).default(obj)
    
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET,PUT,DELETE"
        },
        "body": json.dumps(body, cls=DecimalEncoder)
    }