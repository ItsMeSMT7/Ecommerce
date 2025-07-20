# backend/app.py
import qrcode
import io
import os

from flask import request, send_file
from urllib.parse import quote # ✅ ADD THIS NEW IMPORT
from flask import Flask,request, send_file
from flask_cors import CORS  # Make sure this import is here



# Initialize the Flask app as before
app = Flask(__name__, static_folder="../static")

# ✅ THE DEFINITIVE FIX: Apply CORS to the entire app.
# This is the most direct way to tell Flask: "For every single route in this
# application, add the 'Access-Control-Allow-Origin: *' header."
CORS(app) 

# ✅ IMPORTANT: Add this line to tell Flask where to save uploaded product images.
# Make sure the 'static/images/products' directory exists.
app.config['UPLOAD_FOLDER'] = 'static/images/products'

# --- Import and Register Blueprints ---
# (The rest of the file remains the same)
from routes.auth_routes import auth_bp
from routes.order_routes import order_bp
from routes.product_routes import product_bp
from routes.admin_routes import admin_bp

app.register_blueprint(auth_bp)
app.register_blueprint(order_bp)
app.register_blueprint(product_bp)
app.register_blueprint(admin_bp)

# ✅ THIS IS THE CORRECTED AND FINAL VERSION OF YOUR QR CODE ENDPOINT
# in backend/app.py
@app.route('/generate_qr')
def generate_qr():
    # --- Read all parameters from the request ---
    upi_id = request.args.get('upi_id')
    payee_name = request.args.get('name')
    amount = request.args.get('amount')
    note = request.args.get('note', 'Asalkar Healthy Hub Order')
    # ✅ 1. READ THE NEW UNIQUE TRANSACTION REFERENCE ID
    transaction_ref = request.args.get('refId')

    # --- Validate that all required parameters are present ---
    # The transaction reference is now mandatory.
    if not all([upi_id, payee_name, amount, transaction_ref]):
        return "Missing required parameters. Required: upi_id, name, amount, refId", 400

    # --- URL-encode all text fields to handle special characters ---
    encoded_payee_name = quote(payee_name)
    encoded_note = quote(note)
    encoded_transaction_ref = quote(transaction_ref)

    # ✅ 2. CONSTRUCT THE UPI STRING WITH THE 'tr' PARAMETER
    # 'tr' is the standard parameter for Transaction Reference ID.
    upi_string = f"upi://pay?pa={upi_id}&pn={encoded_payee_name}&am={amount}&cu=INR&tr={encoded_transaction_ref}"
    
    print(f"DEBUG: Generating QR for final UPI string: {upi_string}")

    # --- Generate and return the QR code image ---
    try:
        qr_img = qrcode.make(upi_string)
        buffer = io.BytesIO()
        qr_img.save(buffer, 'PNG')
        buffer.seek(0)
        return send_file(buffer, mimetype='image/png')
    except Exception as e:
        print(f"Error generating QR code: {e}")
        return "Failed to generate QR code", 500

@app.route("/")
def home():
    return "✅ Asalkar Healthy Hub Backend Running"

if __name__ == "__main__":
    app.run(debug=True, port=5000)
    
if __name__ == "__main__":
    # Ensure the upload folder exists when the app starts
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(debug=True, port=5000)