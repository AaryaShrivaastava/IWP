import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from firebase_admin import credentials, firestore, initialize_app
import google.auth
from google.cloud.firestore_v1 import Increment
import logging
from google.api_core.exceptions import ServiceUnavailable

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Set up logging
logging.basicConfig(level=logging.INFO)
logging.getLogger('google.cloud.firestore').setLevel(logging.WARNING)

# Check if running in the Canvas environment
if 'GAE_ENV' in os.environ and os.environ['GAE_ENV'] == 'standard':
    # Production environment (Google App Engine)
    # The Admin SDK will automatically find the credentials
    cred = credentials.ApplicationDefault()
    initialize_app(cred)
    logging.info("Firebase initialized with Application Default Credentials.")
else:
    # Local development or Canvas
    logging.info("Initializing Firebase with local credentials.")
    try:
        if '__firebase_config' in locals() or '__firebase_config' in globals():
            firebase_config = globals().get('__firebase_config')
            firebase_config = firebase_config.replace("'", "\"") # Replace single quotes with double quotes
            firebase_config = firebase_config.replace("True", "true").replace("False", "false") # Replace Python booleans with JavaScript booleans
            firebase_config = eval(firebase_config)
            cred = credentials.Certificate(firebase_config)
        else:
            # Fallback for when __firebase_config is not available
            raise FileNotFoundError("Firebase config not found.")
        initialize_app(cred)
        logging.info("Firebase initialized successfully with provided config.")
    except Exception as e:
        logging.error(f"Failed to initialize Firebase with provided config: {e}")

db = firestore.client()

@app.route('/track', methods=['POST'])
def track():
    """
    Receives anonymous tracking data and updates aggregated page view counts in Firestore.
    """
    try:
        data = request.get_json()
        page_path = data.get('path')
        screen_resolution = data.get('resolution')

        if not page_path:
            logging.warning("Missing 'path' in request data.")
            return jsonify({"error": "Missing 'path'"}), 400

        # Create a reference to the 'page_views' collection
        collection_path = 'analytics'
        doc_ref = db.collection(collection_path).document('page_views')
        
        # Use a transaction to ensure atomic updates
        @firestore.transactional
        def update_in_transaction(transaction, doc_ref, page_path):
            snapshot = doc_ref.get(transaction=transaction)
            if snapshot.exists:
                # Document exists, update it
                current_views = snapshot.get(page_path) or 0
                transaction.update(doc_ref, {page_path: current_views + 1, 'total_views': Increment(1)})
            else:
                # Document doesn't exist, create it
                transaction.set(doc_ref, {page_path: 1, 'total_views': 1})
            
            logging.info(f"Updated page views for path: {page_path}")
            
        update_in_transaction(db.transaction(), doc_ref, page_path)

        return jsonify({"message": "Tracking data received"}), 200

    except ServiceUnavailable:
        logging.error("Firestore service is unavailable. Retrying the request.")
        return jsonify({"error": "Service unavailable"}), 503
    except Exception as e:
        logging.error(f"An error occurred: {e}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
