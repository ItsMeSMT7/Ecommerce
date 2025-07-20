from flask import Blueprint, request, jsonify
from config import db 
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__)
users_collection = db["User"]

@auth_bp.route("/api/signup", methods=["POST"])
def signup():
    data = request.form
    name = data.get("name")
    contact = data.get("contact")
    email = data.get("email")
    address = data.get("address")
    password = data.get("password")

    if not all([name, contact, email, address, password]):
        return jsonify({"success": False, "message": "All fields are required"}), 400
    if users_collection.find_one({"email": email}):
        return jsonify({"success": False, "message": "User already exists"}), 409

    hashed_password = generate_password_hash(password)
    users_collection.insert_one({
        "name": name, "contact": contact, "email": email, "address": address, "password": hashed_password
    })
    return jsonify({"success": True, "message": "Signup successful"}), 201

@auth_bp.route("/api/login", methods=["POST"])
def login():
    identifier = request.form.get("identifier")
    password = request.form.get("password")

    if not identifier or not password:
        return jsonify({"success": False, "message": "Email/contact and password are required"}), 400

    user = users_collection.find_one({"$or": [{"email": identifier}, {"contact": identifier}]})

    if user and check_password_hash(user["password"], password):
        return jsonify({
            "success": True, "name": user["name"], "email": user["email"], "contact": user["contact"]
        })
    else:
        return jsonify({"success": False, "message": "Invalid credentials."}), 401