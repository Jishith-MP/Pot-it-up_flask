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

# Route to create an order
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