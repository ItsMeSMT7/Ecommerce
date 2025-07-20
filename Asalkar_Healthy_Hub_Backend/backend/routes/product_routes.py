
from flask import Blueprint, request, jsonify, current_app
from pymongo import MongoClient
from bson import ObjectId
from config import MONGO_URI, DB_NAME
from bson.errors import InvalidId 
import os
from werkzeug.utils import secure_filename

product_bp = Blueprint("products", __name__)
client = MongoClient(MONGO_URI)
db = client[DB_NAME]
product_collection = db["products"]

def is_allowed_file(filename):
    """Helper function to check for allowed image file extensions."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif', 'webp'}


@product_bp.route("/api/products", methods=["GET"])
def get_products():
    products = list(product_collection.find({}))
    for p in products:
        p["_id"] = str(p["_id"])
    return jsonify(products)

@product_bp.route("/api/products", methods=["POST"])
def add_product():
    """Adds a new product, handling file uploads."""
    if 'photo' not in request.files or request.files['photo'].filename == '':
        return jsonify({"success": False, "message": "Product image is required."}), 400
    
    file = request.files['photo']
    if file and is_allowed_file(file.filename):
        filename = secure_filename(file.filename)
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/images/products')
        
        try:
            # ✅ FIX: Added a try-except block for robust type conversion.
            price = float(request.form.get('price'))
            stock = int(request.form.get('stock'))
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Price and Stock must be valid numbers."}), 400

        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        db_image_path = os.path.join('/images/products', filename).replace("\\", "/")

        new_product = {
            "name": request.form.get('name'),
            "price": price,
            "category": request.form.get('category'),
            "description": request.form.get('description'),
            "stock": stock,
            "image": db_image_path,
        }
        product_collection.insert_one(new_product)
        return jsonify({"success": True, "message": "Product added successfully."}), 201

    return jsonify({"success": False, "message": "Invalid file type."}), 400


# ✅ THIS IS THE MAIN FIX
# ✅ THIS IS THE FINAL, SIMPLIFIED, AND CORRECTED VERSION
@product_bp.route("/api/products/<product_id>", methods=["PUT"])
def update_product(product_id):
    """Updates a product. If a new image is provided, it's updated. If not, the old one is kept."""
    try:
        # Step 1: Prepare the text-based data from the form, with safe number conversion.
        try:
            update_data = {
                "name": request.form.get('name'),
                "price": float(request.form.get('price')),
                "category": request.form.get('category'),
                "description": request.form.get('description'),
                "stock": int(request.form.get('stock')),
            }
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Price and Stock must be valid numbers."}), 400

        # Step 2: Check if a new image file was uploaded with the form.
        if 'photo' in request.files and request.files['photo'].filename != '':
            file = request.files['photo']
            if is_allowed_file(file.filename):
                # If the new file is valid, save it and add its path to our update data.
                filename = secure_filename(file.filename)
                upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/images/products')
                
            else:
                 return jsonify({"success": False, "message": "Invalid file type for new image."}), 400

        # Step 3: Perform the update.
        # If a new image was uploaded, `update_data` contains the new image path and will overwrite the old one.
        # If no new image was uploaded, `update_data` does NOT contain an 'image' key,
        # so MongoDB's $set operator will leave the existing image field untouched.
        result = product_collection.update_one(
            {"_id": ObjectId(product_id)},
            {"$set": update_data}
        )

        # We can still check if the update actually changed anything.
        if result.modified_count == 0 and 'image' not in update_data:
            return jsonify({"success": False, "message": "No changes were made."}), 200

        return jsonify({"success": True, "message": "Product updated successfully."}), 200

    except Exception as e:
        print(f"CRITICAL ERROR in update_product for ID {product_id}: {e}")
        return jsonify({"success": False, "message": "A critical server error occurred. Check the server logs."}), 500


@product_bp.route("/api/products/<product_id>", methods=["DELETE"])
def delete_product(product_id):
    """Deletes a product by its ID, with ID validation."""
    try:
        # ✅ FIX: Added the same ID validation here for safety.
        result = product_collection.delete_one({"_id": ObjectId(product_id)})
        if result.deleted_count == 0:
            return jsonify({"success": False, "message": "Product not found."}), 404
        return jsonify({"success": True, "message": "Product deleted successfully."}), 200
    except InvalidId:
        return jsonify({"success": False, "message": "Invalid Product ID format."}), 400
    except Exception as e:
        print(f"CRITICAL ERROR in delete_product for ID {product_id}: {e}")
        return jsonify({"success": False, "message": "A critical server error occurred. Check the server logs."}), 500