from flask import Flask, request, jsonify
import razorpay
import uuid
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Access environment variables
api_key = os.getenv('RAZORPAY_API_KEY')
api_secret = os.getenv('RAZORPAY_API_SECRET')

# Initialize Razorpay client
client = razorpay.Client(auth=(api_key, api_secret))

# Route to create invoice
@app.route('/create-invoice', methods=['POST'])
def create_invoice():
    try:
        data = request.get_json()
        orderid = data.get('orderid')
        uid = data.get('uid')
        productCodes = data.get('productCodes')
        productQuantities = data.get('productQuantities')
        products = data.get('products')

        # Validate required fields
        if not orderid or not uid or not productCodes or not products:
            return jsonify({'error': 'Missing required data'}), 400

        # Simulating user details fetch (replace with actual DB query)
        customer_name = 'John Doe'  # Example, replace with actual user data
        customer_email = 'john@example.com'
        customer_contact = '9876543210'

        # Prepare line_items and calculate total amount
        line_items = []
        total_amount = 0

        # Process each product code from the productCodes array
        for i, productCode in enumerate(productCodes):
            # Fetch the product from the provided products object
            product = next((p for key, p in products.items() if p['code'] == productCode), None)
            
            if product:
                # Create line item for each product
                line_items.append({
                    'name': product['name'],
                    'description': product['description'],
                    'amount': product['discounted_price'] * 100,  # Convert to paise
                    'currency': 'INR',
                    'quantity': productQuantities[i]
                })
                # Add the product total price to the overall amount (in paise)
                total_amount += product['discounted_price'] * productQuantities[i] * 100
            else:
                return jsonify({'error': f'Product with code {productCode} not found'}), 404

        # Create invoice data for Razorpay
        invoice_data = {
            'type': 'invoice',
            'customer': {
                'name': customer_name,
                'email': customer_email,
                'contact': customer_contact
            },
            'line_items': line_items,
            'expire_by': 1735689600,  # Expiration timestamp
            'currency': 'INR',
            'sms_notify': 1,
            'email_notify': 1,
            'receipt': orderid,
            'description': f'Invoice for order {orderid}',
            'terms': 'No returns, replacements, or refunds.',
            'partial_payment': False
        }

        # Create the Razorpay invoice
        invoice = client.invoice.create(data=invoice_data)

        # Return the invoice details, including the short URL for viewing the invoice
        return jsonify({'success': True, 'invoice': invoice, 'short_url': invoice['short_url']}), 200

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
