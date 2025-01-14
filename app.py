from flask import Flask, request, jsonify, send_file
import razorpay
import uuid
from flask_cors import CORS
from dotenv import load_dotenv
import os
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Load environment variables
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

    amount_in_paise = int(fin_total * 100)
    receipt = str(uuid.uuid4())

    order_data = {
        'amount': amount_in_paise,
        'currency': 'INR',
        'payment_capture': '1',
        'receipt': receipt
    }

    try:
        order = client.order.create(data=order_data)
        return jsonify({'id': order['id'], 'receipt': receipt})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to verify payment
@app.route('/verify-payment', methods=['POST'])
def verify_payment():
    payment_id = request.json.get('payment_id')

    if not payment_id:
        return jsonify({'error': 'Payment ID is required'}), 400

    try:
        payment = client.payment.fetch(payment_id)
        if payment['status'] == 'captured':
            return jsonify({"success": True, "message": "Payment verified successfully!"})
        else:
            return jsonify({"success": False, "message": "Payment failed!"})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Route to create invoice
@app.route('/create-invoice', methods=['POST'])
def create_invoice():
    try:
        data = request.get_json()
        invoice_data = {
            "invoice_number": data.get('invoice_number'),
            "date_of_issue": datetime.now().strftime("%d/%m/%Y"),
            "seller": data.get('seller'),
            "buyer": data.get('buyer'),
            "products": data.get('products'),
            "total_amount": data.get('total_amount'),
            "payment_method": data.get('payment_method'),
            "terms_conditions": data.get('terms_conditions'),
        }

        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        c.setFont("Helvetica", 12)

        c.drawString(200, 750, "Invoice")
        c.drawString(30, 730, f"Invoice Number: {invoice_data['invoice_number']}")
        c.drawString(30, 710, f"Date of Issue: {invoice_data['date_of_issue']}")

        c.drawString(30, 690, "Seller Information:")
        c.drawString(30, 670, f"Name: {invoice_data['seller']['name']}")
        c.drawString(30, 650, f"Phone: {invoice_data['seller']['phone']}")
        c.drawString(30, 630, f"Email: {invoice_data['seller']['email']}")
        c.drawString(30, 610, f"Website: {invoice_data['seller']['website']}")

        c.drawString(30, 590, "Buyer Information:")
        c.drawString(30, 570, f"Name: {invoice_data['buyer']['name']}")
        c.drawString(30, 550, f"Phone: {invoice_data['buyer']['phone']}")
        c.drawString(30, 530, f"Email: {invoice_data['buyer']['email']}")
        c.drawString(30, 510, f"Address: {invoice_data['buyer']['address']}")

        c.drawString(30, 490, "Products:")
        y_position = 470
        c.drawString(30, y_position, "Product")
        c.drawString(200, y_position, "Quantity")
        c.drawString(300, y_position, "Unit Price (INR)")
        c.drawString(400, y_position, "Amount (INR)")

        y_position -= 20
        for product in invoice_data['products']:
            if y_position < 100:
                c.showPage()
                y_position = 750
            c.drawString(30, y_position, product['name'])
            c.drawString(200, y_position, str(product['quantity']))
            c.drawString(300, y_position, str(product['unit_price']))
            c.drawString(400, y_position, str(product['amount']))
            y_position -= 20

        c.drawString(30, y_position, f"Total Amount: ₹{invoice_data['total_amount']}")
        c.drawString(30, y_position - 20, f"Payment Method: {invoice_data['payment_method']}")
        c.drawString(30, y_position - 40, f"Terms and Conditions: {invoice_data['terms_conditions']}")

        c.save()
        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name=f"invoice_{invoice_data['invoice_number']}.pdf", mimetype='application/pdf')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
