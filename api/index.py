# This is the Python Flask backend API.
# It receives anonymous tracking data and updates the Firestore database.
# It does not log IP addresses or store any personal information.

from flask import Flask, request, jsonify
from flask_cors import CORS
import firebase_admin
from firebase_admin import credentials, firestore
import os
import datetime

# Initialize the Flask app
app = Flask(__name__)
# Enable CORS for all origins, as the tracker will be on a different domain
CORS(app)

# --- Firebase Admin SDK Setup ---
# NOTE: Replace 'path/to/your/serviceAccountKey.json' with the actual path
# to your Firebase Admin SDK service account key file.
# You must download this JSON file from your Firebase project settings.
# For security, store this file securely and do not commit it to version control.
# A common practice is to use an environment variable to point to the file path.
cred = credentials.Certificate("serviceAccountKey.json")
try:
    firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    print(f"Failed to initialize Firebase Admin SDK: {e}")
    db = None

@app.route('/track', methods=['POST'])
def track_page_view():
    """
    Endpoint to receive and process anonymous page view data.
    """
    if db is None:
        print("Database not initialized. Cannot process request.")
        return jsonify({"status": "error", "message": "Database not available"}), 503

    try:
        # Get the JSON data from the request body
        data = request.json
        if not data or 'pagePath' not in data:
            return jsonify({"status": "error", "message": "Invalid data"}), 400

        page_path = data['pagePath']
        # You could also use screenWidth and screenHeight here if needed
        # For example, to aggregate data by device type.

        # Use Firestore to increment a counter for the page and for total views
        # The data is aggregated and does not store individual sessions.
        
        # Reference to the analytics document for the specific page
        # This will be created if it doesn't exist.
        page_doc_ref = db.collection('analytics').document('pages').collection('views').document(page_path.replace('/', '_'))
        
        # Reference to the total views counter
        total_views_doc_ref = db.collection('analytics').document('total')
        
        # Use a Firestore transaction to ensure both increments are atomic
        @firestore.transactional
        def update_in_transaction(transaction):
            # Get the current state of both documents
            page_doc = page_doc_ref.get(transaction=transaction)
            total_doc = total_views_doc_ref.get(transaction=transaction)

            # Update the page view count
            if page_doc.exists:
                new_count = page_doc.get('count') + 1
                transaction.update(page_doc_ref, {'count': new_count})
            else:
                transaction.set(page_doc_ref, {'count': 1})
            
            # Update the total views count
            if total_doc.exists:
                new_total = total_doc.get('count') + 1
                transaction.update(total_views_doc_ref, {'count': new_total})
            else:
                transaction.set(total_views_doc_ref, {'count': 1})
        
        # Run the transaction
        transaction = db.transaction()
        update_in_transaction(transaction)
        
        print(f"Successfully tracked a view for: {page_path}")
        return jsonify({"status": "success", "message": "Data tracked successfully"}), 200

    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500

if __name__ == '__main__':
    # Use '0.0.0.0' to make the server accessible from outside the container
    # This is for development purposes only.
    app.run(host='0.0.0.0', port=5000, debug=True)
