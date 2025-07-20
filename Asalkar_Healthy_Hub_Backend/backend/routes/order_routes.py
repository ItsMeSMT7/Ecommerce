# backend/routes/order_routes.py

from flask import Blueprint, request, jsonify
from pymongo.errors import PyMongoError
from config import db
from bson.objectid import ObjectId
# ✅ ADD THE LINE HERE, WITH THE OTHER IMPORTS
from utils.email_utils import send_delivery_email, send_confirmation_email, send_cancellation_email
from datetime import datetime

order_bp = Blueprint("orders", __name__)

# ✅ We only define the collections we actually use.
orders_collection = db["orders"]
products_collection = db["products"]


# ✅ POST: Place Order (Final Simplified Version)
@order_bp.route("/api/order/place", methods=["POST"])
def place_order():
    data = request.json
    required_fields = ["name", "contact", "email", "address", "payment", "items"]
    if not all(data.get(field) for field in required_fields):
        return jsonify({"success": False, "message": "Missing required fields"}), 400

    try:
        # Step 1: Check stock for all items
        for item in data["items"]:
            product = products_collection.find_one({"_id": ObjectId(item["id"])})
            if not product:
                return jsonify({"success": False, "message": f"Product '{item['name']}' not found."}), 404
            if product.get("stock", 0) < item["quantity"]:
                return jsonify({
                    "success": False,
                    "message": f"Sorry, '{item['name']}' is out of stock. Only {product.get('stock', 0)} left."
                }), 400

        # Step 2: If checks pass, deduct stock
        for item in data["items"]:
            products_collection.update_one(
                {"_id": ObjectId(item["id"])},
                {"$inc": {"stock": -item["quantity"]}}
            )

        # Step 3: Calculate the total amount and add final details to the order data
        total_amount = sum(item['price'] * item['quantity'] for item in data['items'])
        data["totalAmount"] = total_amount
        data["status"] = "Pending"
        data["orderDate"] = datetime.utcnow()

        # Step 4: Save the single, enriched order record to the primary 'orders' collection
        order_result = orders_collection.insert_one(data)
        data['_id'] = order_result.inserted_id # Add the new ID for the email function

        # Step 5: Send confirmation email
        send_confirmation_email(data)

        return jsonify({"success": True, "message": "Order placed successfully!"}), 201

    except PyMongoError as e:
        print(f"A database error occurred: {e}")
        return jsonify({"success": False, "message": "A server error occurred. Please try again."}), 500


# GET: Fetch All Orders (for Admin)
@order_bp.route("/api/orders", methods=["GET"])
def get_orders():
    orders = list(orders_collection.find().sort("orderDate", -1))
    for order in orders:
        order["_id"] = str(order["_id"])
        if 'orderDate' in order and isinstance(order['orderDate'], datetime):
            order['orderDate'] = order['orderDate'].isoformat()
    return jsonify(orders)

# PATCH: Mark Order Delivered
@order_bp.route("/api/orders/<order_id>/deliver", methods=["PATCH"])
def mark_order_delivered(order_id):
    order = orders_collection.find_one({"_id": ObjectId(order_id)})
    if not order: return jsonify({"success": False, "message": "Order not found."}), 404
    result = orders_collection.update_one({"_id": ObjectId(order_id)}, {"$set": {"status": "Delivered"}})
    if result.modified_count == 0: return jsonify({"success": False, "message": "Order was already marked as delivered."}), 400
    if order.get("email"): send_delivery_email(order)
    return jsonify({"success": True, "message": "Order marked as delivered and user notified."})

# GET All Orders for a Specific User
@order_bp.route("/api/user/orders", methods=["POST"])
def get_user_orders():
    data = request.json
    user_email = data.get("email")
    if not user_email: return jsonify({"success": False, "message": "User email is required."}), 400
    user_orders = list(orders_collection.find({"email": user_email}).sort("orderDate", -1))
    for order in user_orders:
        order["_id"] = str(order["_id"])
        if 'orderDate' in order and isinstance(order['orderDate'], datetime):
            order['orderDate'] = order['orderDate'].isoformat()
    return jsonify({"success": True, "orders": user_orders})

# DELETE: Delete Order by ID
# REPLACE the old delete_order function with this corrected version

# REPLACE the old delete_order function with this new, more robust version.

@order_bp.route("/api/orders/<order_id>", methods=["DELETE"])
def delete_order(order_id):
    try:
        # Find the order to get user details for the email
        order = orders_collection.find_one({"_id": ObjectId(order_id)})
        if not order:
            return jsonify({"success": False, "message": "Order not found."}), 404

        # Check if the order is already canceled to avoid re-sending emails
        if order.get("status") == "Canceled":
            return jsonify({"success": False, "message": "This order has already been canceled."}), 400

        # Update the status to "Canceled" in the database
        result = orders_collection.update_one(
            {"_id": ObjectId(order_id)},
            {"$set": {"status": "Canceled"}}
        )

        # Send the cancellation email only after a successful update
        if result.modified_count > 0:
            if order.get("email"):
                # ✅ ADDED LOGGING: This will print to your Flask console
                print(f"--- Attempting to send cancellation email to {order.get('email')} ---")
                send_cancellation_email(order)
            return jsonify({"success": True, "message": "!!! BACKEND TEST SUCCESSFUL - Now check the Flask console for email logs."})
        else:
            # This case should rarely be hit now, but it's good for safety
            return jsonify({"success": False, "message": "Failed to update the order status."}), 500

    except Exception as e:
        # Catch any other unexpected errors and report them
        print(f"An error occurred while canceling order {order_id}: {e}")
        return jsonify({"success": False, "message": "An unexpected server error occurred."}), 500