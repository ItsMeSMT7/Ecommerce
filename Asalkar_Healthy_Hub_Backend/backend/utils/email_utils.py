import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()

SENDER_EMAIL = os.getenv("MAIL_USERNAME")
SENDER_PASSWORD = os.getenv("MAIL_PASSWORD")

# Replace the existing send_email function with this one

def send_email(receiver_email, subject, body):
    print("--- 1. 'send_email' function has been called. ---") # New log
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("❌ FATAL ERROR: Email credentials not set in .env file. Cannot send email.")
        print("   -> Check your backend/.env file for MAIL_USERNAME and MAIL_PASSWORD.")
        return
    
    print(f"--- 2. Preparing to send email from '{SENDER_EMAIL}' to '{receiver_email}' ---") # New log
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = receiver_email
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            print("--- 3. Connecting to SMTP server... ---") # New log
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            print("--- 4. SMTP Login successful. ---") # New log
            server.sendmail(SENDER_EMAIL, receiver_email, msg.as_string())
        print(f"✅ SUCCESS: Email sent to {receiver_email}")
    except Exception as e:
        print(f"❌ FATAL ERROR: Email failed to send. The error is: {e}")
        print("   -> COMMON FIXES: ")
        print("      1. Is MAIL_PASSWORD a 16-digit Google App Password (not your regular password)?")
        print("      2. Is 'Less secure app access' enabled for your Google account (if not using App Password)?")
        print("      3. Is there a typo in your MAIL_USERNAME?")

def send_confirmation_email(order):
    total = sum(item['price'] * item['quantity'] for item in order['items'])
    items_list = "\n".join([f"- {i['name']} (x{i['quantity']})" for i in order['items']])
    subject = f"🎉 Order Confirmed: Your Asalkar Healthy Hub Order #{str(order['_id'])[-6:]}"
    body = f"""
Hi {order['name']},

Thank you for your order! We've received it and are getting it ready for delivery.

📦 Order Summary:
Order ID: ...{str(order['_id'])[-6:]}
Total Amount: ₹{total:.2f}
Payment Method: {order['payment']}

Items:
{items_list}

Delivery Address:
{order['address']}

We'll notify you again once your order has been delivered.

Thanks,
The Asalkar Healthy Hub Team
"""
    send_email(order.get("email"), subject, body)

def send_delivery_email(order):
    subject = "✅ Your Asalkar Healthy Hub Order Has Been Delivered!"
    body = f"""
Hi {order['name']},

Great news! Your order has been successfully delivered to:
{order['address']}

We hope you enjoy the pure goodness of our products!

Thank you for shopping with us. We look forward to serving you again.

Thanks,
The Asalkar Healthy Hub Team
"""
    send_email(order.get("email"), subject, body)
    
# Add this new function to email_utils.py
def send_cancellation_email(order):
    # ✅ FIX: Define the missing variables `items_list` and `total`
    total = sum(item['price'] * item['quantity'] for item in order['items'])
    items_list = "\n".join([f"- {i['name']} (x{i['quantity']})" for i in order['items']])

    subject = f"❗️ Regarding Your Asalkar Healthy Hub Order #{str(order['_id'])[-6:]}"
    body = f"""
Hi {order['name']},

We are writing to inform you that your recent order has been canceled.

Order ID: ...{str(order['_id'])[-6:]}
Total Amount: ₹{total:.2f}

Items:
{items_list}

This is typically due to unforeseen stock issues or a problem with the delivery address provided.

If you believe this was in error or have any questions, please do not hesitate to contact us. We apologize for any inconvenience this may cause.

We appreciate your understanding.

Thanks,
The Asalkar Healthy Hub Team
"""
    send_email(order.get("email"), subject, body)