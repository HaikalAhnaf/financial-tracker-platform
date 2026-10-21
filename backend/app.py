import json
import os
import boto3
import base64
import time
from datetime import datetime, timedelta
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses', region_name=os.environ.get('AWS_REGION', 'ap-southeast-1'))
table_name = os.environ.get('DYNAMODB_TABLE', 'FinancialTracker')
table = dynamodb.Table(table_name)

SENDER_EMAIL = "Financial Tracker <no-reply@haikalahnaf.my.id>"

def extract_user_id(event):
    """Decodes JWT and determines if this is a permanent user or a temporary guest session"""
    headers = {k.lower(): v for k, v in event.get('headers', {}).items()}
    auth_header = headers.get('authorization', '')
    if not auth_header.startswith('Bearer '): raise ValueError("Missing Auth header")
    
    token = auth_header.split(' ')[1]
    payload_part = token.split('.')[1]
    payload_part += '=' * ((4 - len(payload_part) % 4) % 4)
    decoded = json.loads(base64.urlsafe_b64decode(payload_part).decode('utf-8'))
    
    email = decoded.get('email')
    if not email: raise ValueError("Invalid token")
    
    guest_session = headers.get('x-guest-session')
    
    # If the demo user logs in AND has a guest session, isolate their data
    if email == 'demo@haikalahnaf.my.id' and guest_session:
        return f"GUEST#{guest_session}", email, True
        
    return f"USER#{email}", email, False

def lambda_handler(event, context):
    print("Received event:", json.dumps(event))
    
    if event.get('source') == 'aws.events':
        return process_automated_reports()

    http_method = event.get('requestContext', {}).get('http', {}).get('method', '')
    
    try:
        if http_method == 'OPTIONS':
            return build_response(200, "CORS Preflight OK")
            
        user_id, user_email, is_guest = extract_user_id(event)
        query_params = event.get('queryStringParameters') or {}
        entity = query_params.get('entity')
        
        if entity == 'settings':
            if http_method == 'GET': return get_settings(user_id)
            if http_method == 'POST': return save_settings(event, user_id, is_guest)
        elif entity == 'report' and http_method == 'POST':
            return generate_and_send_report(user_id, user_email)
        elif entity == 'category':
            if http_method == 'POST': return create_category(event, user_id, is_guest)
            if http_method == 'GET': return get_categories(user_id)
            if http_method == 'DELETE': return delete_category(event, user_id)
        else:
            if http_method == 'POST': return create_transaction(event, user_id, user_email, is_guest)
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
# REPORTING & SETTINGS LOGIC
# ==========================================
def get_settings(user_id):
    response = table.get_item(Key={'PK': user_id, 'SK': 'SETTINGS'})
    settings = response.get('Item', {'reports_enabled': False, 'report_emails': []})
    return build_response(200, {"settings": settings})

def save_settings(event, user_id, is_guest=False):
    body = json.loads(event.get('body', '{}'))
    item = {
        'PK': user_id,
        'SK': 'SETTINGS',
        'reports_enabled': body.get('reports_enabled', False),
        'report_emails': body.get('report_emails', []),
        'budget_limit': int(body.get('budget_limit', 0)),         
        'budget_threshold': int(body.get('budget_threshold', 0))  
    }
    
    if is_guest:
        item['expire_at'] = int(time.time()) + 86400 # 24 hours TTL
        
    table.put_item(Item=item)
    return build_response(200, {"message": "Settings saved", "settings": item})

def process_automated_reports():
    response = table.scan(FilterExpression="SK = :sk AND reports_enabled = :true", ExpressionAttributeValues={":sk": "SETTINGS", ":true": True})
    for user_settings in response.get('Items', []):
        user_id = user_settings['PK']
        # Do not send automated reports for guest sessions
        if not user_id.startswith("GUEST#"):
            user_email = user_id.split('#')[1]
            generate_and_send_report(user_id, user_email, is_automated=True)
    return {"statusCode": 200, "body": "Automated reports processed"}

def generate_and_send_report(user_id, user_email, is_automated=False):
    response = table.get_item(Key={'PK': user_id, 'SK': 'SETTINGS'})
    settings = response.get('Item', {})
    emails_to_send = settings.get('report_emails', [user_email])
    
    if not emails_to_send:
        return build_response(400, {"error": "No email addresses configured."})

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
        ses.send_email(
            Source=SENDER_EMAIL,
            Destination={'ToAddresses': emails_to_send},
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body_text}}
            }
        )
        return build_response(200, {"message": "Report sent successfully!"})
    except Exception as e:
        print("SES Error:", e)
        return build_response(500, {"error": "Failed to send email.", "details": str(e)})

def check_and_trigger_budget_alert(user_id, user_email, new_txn_amount, timestamp):
    response = table.get_item(Key={'PK': user_id, 'SK': 'SETTINGS'})
    settings = response.get('Item', {})
    
    threshold = int(settings.get('budget_threshold', 0))
    limit = int(settings.get('budget_limit', 0))
    emails_to_send = settings.get('report_emails', [user_email])
    
    if threshold <= 0: return 
    
    month_str = timestamp[:7] 
    txn_response = table.query(
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_val)",
        ExpressionAttributeValues={":pk": user_id, ":sk_val": f"TXN#{month_str}"}
    )
    txns = txn_response.get('Items', [])
    current_expense = sum([Decimal(t['amount']) for t in txns if t['type'] == 'expense'])
    
    old_expense = current_expense - Decimal(new_txn_amount)
    
    if old_expense < Decimal(threshold) and current_expense >= Decimal(threshold):
        subject = f"⚠️ Budget Alert: You crossed Rp {threshold} in expenses!"
        body_text = f"Warning!\n\nYour expenses for {month_str} have just reached Rp {current_expense}.\nThis crosses your set alarm threshold of Rp {threshold} (Monthly limit: Rp {limit}).\n\nPlease check your Financial Tracker dashboard."
        
        try:
            ses.send_email(
                Source=SENDER_EMAIL,
                Destination={'ToAddresses': emails_to_send},
                Message={
                    'Subject': {'Data': subject},
                    'Body': {'Text': {'Data': body_text}}
                }
            )
        except Exception as e:
            print("SES Budget Alert Error:", e)

# ==========================================
# TRANSACTION LOGIC
# ==========================================
def create_transaction(event, user_id, user_email, is_guest=False):
    body = json.loads(event.get('body', '{}'))
    timestamp = body.get('date', datetime.utcnow().isoformat()) + 'Z'
    sk = f"TXN#{timestamp}"
    
    item = {
        'PK': user_id,
        'SK': sk,
        'type': body['type'],
        'amount': str(body['amount']),
        'category': body['category'],
        'note': body.get('note', ''),
        'timestamp': timestamp
    }
    
    if is_guest:
        item['expire_at'] = int(time.time()) + 86400 # 24 hours TTL
        
    table.put_item(Item=item)
    
    if body['type'] == 'expense' and not is_guest:
        check_and_trigger_budget_alert(user_id, user_email, body['amount'], timestamp)
        
    return build_response(200, {"message": "Transaction created", "transaction": item})

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
    if not response.get('Item'):
        return build_response(404, {"error": "Transaction not found"})
        
    table.delete_item(Key={'PK': user_id, 'SK': sk_to_delete})
    return build_response(200, {"message": "Transaction deleted"})

def get_transactions(event, user_id):
    query_params = event.get('queryStringParameters') or {}
    month = query_params.get('month')
    start_date = query_params.get('startDate')
    end_date = query_params.get('endDate')
    time_range = query_params.get('range')
    
    try:
        if start_date and end_date:
            start_sk = f"TXN#{start_date}"
            end_sk = f"TXN#{end_date}T23:59:59" 
            response = table.query(
                KeyConditionExpression="PK = :pk AND SK BETWEEN :start_sk AND :end_sk",
                ExpressionAttributeValues={":pk": user_id, ":start_sk": start_sk, ":end_sk": end_sk}
            )
        elif month:
            response = table.query(
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_val)",
                ExpressionAttributeValues={":pk": user_id, ":sk_val": f"TXN#{month}"}
            )
        else:
            if time_range == '1m': days_ago = 30
            elif time_range == '3m': days_ago = 90
            elif time_range == '1y': days_ago = 365
            else: days_ago = 180 
            
            past_date = (datetime.utcnow() - timedelta(days=days_ago)).strftime('%Y-%m-%dT%H:%M:%S')
            start_sk = f"TXN#{past_date}"
            
            response = table.query(
                KeyConditionExpression="PK = :pk AND SK >= :start_sk",
                ExpressionAttributeValues={":pk": user_id, ":start_sk": start_sk}
            )
            
        items = response.get('Items', [])
        balance = sum([Decimal(t['amount']) if t['type'] == 'income' else -Decimal(t['amount']) for t in items])
        
        return build_response(200, {"balance": balance, "transactions": items})
        
    except Exception as e:
        print("Error fetching transactions:", e)
        return build_response(500, {"error": "Failed to fetch transactions"})
    
# ==========================================
# CATEGORY LOGIC
# ==========================================
def create_category(event, user_id, is_guest=False):
    body = json.loads(event.get('body', '{}'))
    name = body.get('name')
    cat_type = body.get('type') 
    
    if not name or not cat_type:
        return build_response(400, {"error": "Category name and type are required"})
        
    sort_key = f"CATEGORY#{cat_type}#{name.lower()}"
    
    item = {
        'PK': user_id,
        'SK': sort_key,
        'name': name,
        'type': cat_type,
        'timestamp': datetime.utcnow().isoformat()
    }
    
    if is_guest:
        item['expire_at'] = int(time.time()) + 86400 # 24 hours TTL
        
    table.put_item(Item=item)
    return build_response(201, {"message": "Category created", "category": item})

def get_categories(user_id):
    response = table.query(
        KeyConditionExpression="PK = :pk AND begins_with(SK, :sk_val)",
        ExpressionAttributeValues={":pk": user_id, ":sk_val": "CATEGORY#"}
    )
    
    categories = response.get('Items', [])
    if not categories:
        # If it is a guest (or new user), generate default TTL categories
        expire = int(time.time()) + 86400 if user_id.startswith("GUEST#") else None
        
        defaults = [
            {'PK': user_id, 'SK': 'CATEGORY#expense#food', 'name': 'Food', 'type': 'expense'},
            {'PK': user_id, 'SK': 'CATEGORY#expense#transport', 'name': 'Transport', 'type': 'expense'},
            {'PK': user_id, 'SK': 'CATEGORY#income#salary', 'name': 'Salary', 'type': 'income'}
        ]
        
        for cat in defaults:
            if expire: cat['expire_at'] = expire
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
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Guest-Session",
            "Access-Control-Allow-Methods": "OPTIONS,POST,GET,PUT,DELETE"
        },
        "body": json.dumps(body, cls=DecimalEncoder)
    }