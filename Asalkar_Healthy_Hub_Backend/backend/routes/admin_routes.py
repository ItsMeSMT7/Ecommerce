from flask import Blueprint, jsonify, request
from config import db
from datetime import datetime # ✅ ADD datetime
from bson.objectid import ObjectId # ✅ FIX: ADD THIS IMPORT

admin_bp = Blueprint("admin", __name__)

# ✅ We'll define the new collection here
inquiries_collection = db["inquiries"]



@admin_bp.route("/api/summary", methods=["GET"])
def get_summary():
    product_count = db['products'].count_documents({})
    order_count = db['orders'].count_documents({})
    user_count = db['User'].count_documents({})
    return jsonify({
        "products": product_count, "orders": order_count, "users": user_count
    })
    
# ✅ ADD THIS NEW ENDPOINT TO SAVE CONTACT MESSAGES
@admin_bp.route("/api/contact/submit", methods=["POST"])
def submit_contact_form():
    data = request.json
    name = data.get("name")
    email = data.get("email")
    message = data.get("message")

    if not all([name, email, message]):
        return jsonify({"success": False, "message": "All fields are required."}), 400
    
    try:
        inquiry = {
            "name": name,
            "email": email,
            "message": message,
            "createdAt": datetime.utcnow(),
            "isRead": False # Optional: for future "mark as read" functionality
        }
        inquiries_collection.insert_one(inquiry)
        return jsonify({"success": True, "message": "Thank you! Your message has been sent."}), 201
    except Exception as e:
        print(f"Error saving inquiry: {e}")
        return jsonify({"success": False, "message": "A server error occurred."}), 500

# ✅ ADD THIS NEW ENDPOINT TO GET ALL INQUIRIES FOR THE ADMIN
@admin_bp.route("/api/inquiries", methods=["GET"])
def get_inquiries():
    try:
        # Sort by newest first
        inquiries = list(inquiries_collection.find({}).sort("createdAt", -1))
        # Convert ObjectId and datetime to string for JSON compatibility
        for inquiry in inquiries:
            inquiry["_id"] = str(inquiry["_id"])
            if 'createdAt' in inquiry:
                inquiry['createdAt'] = inquiry['createdAt'].isoformat()
        return jsonify(inquiries)
    except Exception as e:
        print(f"Error fetching inquiries: {e}")
        return jsonify({"success": False, "message": "Could not fetch inquiries."}), 500

# ✅ ADD THIS NEW ENDPOINT TO DELETE AN INQUIRY
# ✅ FIX: Removed duplicated route decorator
@admin_bp.route("/api/inquiries/<inquiry_id>", methods=["DELETE"])
def delete_inquiry(inquiry_id):
    try:
        result = inquiries_collection.delete_one({"_id": ObjectId(inquiry_id)})
        if result.deleted_count == 0:
            return jsonify({"success": False, "message": "Inquiry not found."}), 404
        return jsonify({"success": True, "message": "Inquiry deleted successfully."}), 200
    except Exception as e:
        print(f"Error deleting inquiry {inquiry_id}: {e}")
        return jsonify({"success": False, "message": "An unexpected server error occurred."}), 500