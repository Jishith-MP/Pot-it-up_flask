from flask import Flask, request, jsonify
import razorpay
import uuid
from flask_cors import CORS
from dotenv import load_dotenv
import os
import time  # Import time library for the current time

# Load environment variables from the .env file
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Access environment variables
api_key = os.getenv('RAZORPAY_API_KEY')
api_secret = os.getenv('RAZORPAY_API_SECRET')

# Initialize Razorpay client
client = razorpay.Client(auth=(api_key, api_secret))

@app.route('/create-invoice', methods=['POST'])
def create_invoice():
    data = request.get_json()
    orderid = data.get('orderid')
    uid = data.get('uid')
    productCodes = data.get('productCodes')
    productQuantities = data.get('productQuantities')
    products = data.get('products')

    if not orderid or not uid or not productCodes or not products:
        return jsonify({'error': 'Missing required data'}), 400

    # Fetch user details from your database using UID (for example Firebase)
    customer_name = 'John Doe'  # Example, replace with actual user data
    customer_email = 'john@example.com'
    customer_contact = '9876543210'

    # Prepare line_items for Razorpay invoice
    line_items = []
    total_amount = 0

    for i, productCode in enumerate(productCodes):
        product = next((p for p in products if p['code'] == productCode), None)
        if product:
            line_items.append({
                'name': product['name'],
                'description': product['description'],
                'amount': product['discounted_price'] * 100,  # Convert to paise
                'currency': 'INR',
                'quantity': productQuantities[i]
            })
            total_amount += product['discounted_price'] * productQuantities[i] * 100  # Total amount in paise

    # Calculate expire_by to be 15 minutes ahead
    expire_by = int(time.time()) + 900  # Current time + 15 minutes (900 seconds)

    # Create invoice data
    invoice_data = {
        'type': 'invoice',
        'customer': {
            'name': customer_name,
            'email': customer_email,
            'contact': customer_contact
        },
        'line_items': line_items,
        'expire_by': expire_by,  # Use calculated expire_by
        'currency': 'INR',
        'sms_notify': 1,
        'email_notify': 1,
        'receipt': orderid,
        'description': 'Invoice for order ' + orderid,
        'terms': 'No returns, replacements, or refunds.',
        'partial_payment': False
    }

    try:
        # Create the Razorpay invoice
        invoice = client.invoice.create(data=invoice_data)

        # Return invoice details with URL
        return jsonify({'success': True, 'invoice': invoice}), 200
    except Exception as e:
        # Log the error for debugging purposes
        print(f"Error creating invoice: {str(e)}")
        return jsonify({'error': str(e)}), 500

# Route to create an order (for testing purposes)
@app.route('/create-order', methods=['POST'])
def create_order():
    data = request.get_json()
    fin_total = data.get('amount')  # Amount in INR
    
    if not fin_total:
        return jsonify({'error': 'Amount is required'}), 400
    
    # Convert to paise (100 paise = 1 INR)
    amount_in_paise = int(fin_total * 100)
    
    # Generate unique receipt ID for this order
    receipt = str(uuid.uuid4())
    
    # Create order data
    order_data = {
        'amount': amount_in_paise,
        'currency': 'INR',
        'payment_capture': '1',  # Automatic capture
        'receipt': receipt
    }
    
    try:
        # Create the Razorpay order
        order = client.order.create(data=order_data)
        # Return only necessary details (like order id)
        return jsonify({'id': order['id'], 'receipt': receipt})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to verify the payment status
@app.route('/verify-payment', methods=['POST'])
def verify_payment():
    payment_id = request.json.get('payment_id')
    
    if not payment_id:
        return jsonify({'error': 'Payment ID is required'}), 400

    try:
        # Fetch the payment details from Razorpay using the payment ID
        payment = client.payment.fetch(payment_id)
        
        # Check if the payment status is 'captured' (which means successful)
        if payment['status'] == 'captured':
            # Payment was successful
            # You can now update your order status in the database
            return jsonify({"success": True, "message": "Payment verified successfully!"})
        else:
            # Payment failed
            return jsonify({"success": False, "message": "Payment failed!"})

    except Exception as e:
        # Handle any errors (e.g., invalid payment ID or API error)
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
