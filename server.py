from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash

app = Flask(__name__)

cred = credentials.Certificate("/home/eyas1shal/mysite/key.json")

firebase_admin.initialize_app(cred)

db = firestore.client()

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('Username')
    password = data.get('Password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # Check if the username is already taken
    users_ref = db.collection('Users')
    query = users_ref.where('Username', '==', username).stream()

    if any(query):
        return jsonify({"error": "Username is already taken"}), 409

    # Create a hashed value for the user
    hash_object = hashlib.sha256(username.encode())
    hashed_value = hash_object.hexdigest()

    # Hash the password
    hashed_password = generate_password_hash(password)

    # Add the user to the Users collection
    user_data = {
        "Username": username,
        "hashed_value": hashed_value,
        "Password": hashed_password
    }

    db.collection('Users').document(hashed_value).set(user_data)

    # Create documents in CombatRecords, RaceRecords, and WarzoneRecords collections
    initial_data = {
        "Level_ID": -1,
        "Time": '99999999',
        "TimeStamp": datetime.utcnow().isoformat(),
        "Username": username
    }

    db.collection('CombatRecords').document(hashed_value).set(initial_data)
    db.collection('RaceRecords').document(hashed_value).set(initial_data)
    db.collection('WarzoneRecords').document(hashed_value).set(initial_data)

    return jsonify({"message": "User registered successfully", "hashed_value": hashed_value}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('Username')
    password = data.get('Password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    # Create a hashed value for the user
    hash_object = hashlib.sha256(username.encode())
    hashed_value = hash_object.hexdigest()

    # Retrieve the user document from the Users collection
    user_ref = db.collection('Users').document(hashed_value)
    user_doc = user_ref.get()

    if not user_doc.exists:
        return jsonify({"error": "Invalid username or password"}), 401

    user_data = user_doc.to_dict()
    stored_password = user_data.get('Password')

    # Verify the password
    if not check_password_hash(stored_password, password):
        return jsonify({"error": "Invalid username or password"}), 401

    return jsonify({"message": "Login successful", "hashed_value": hashed_value}), 200


@app.route('/get-all-race-data', methods=['GET'])
def get_all_data():
    records = []
    docs = db.collection('RaceRecords').stream()

    for doc in docs:
        records.append(doc.to_dict())

    return jsonify(records), 200


@app.route('/get-data', methods=['POST'])
def get_data_race():
    data = request.json
    document_name = data.get('document_name')
    colc = data.get('col')
    if not document_name:
        return jsonify({"error": "User required"}), 400

    doc_ref = db.collection(colc).document(document_name)
    doc = doc_ref.get()
    if doc.exists:
        return jsonify(doc.to_dict()), 200
    else:
        return jsonify({"error": "User not found"}), 404

#this is not needed any more, done in reg
# @app.route('/add-record-race', methods=['POST'])
# def add_record():
#     time = request.headers.get('time')
#     if not time:
#         return jsonify({"error": "Time header missing"}), 400

#     # Hardcoded values
#     level_id = 1
#     user_id = 1

#     # Generate the current timestamp
#     timestamp = datetime.utcnow().isoformat()

#     # Create the new record
#     new_record = {
#         "Level_ID": level_id,
#         "User_ID": user_id,
#         "Time": time,
#         "TimeStamp": timestamp
#     }

#     # Add the record to Firestore
#     doc_ref = db.collection('RaceRecords').add(new_record)

#     return jsonify({"message": "Record added", "id": doc_ref[1].id}), 201

@app.route('/update-record', methods=['PUT'])
def update_record():
    data = request.json
    document_name = data.get('document_name')
    colc= data.get('colc')
    time = request.headers.get('time')
    if not time:
        return jsonify({"error": "Time header missing"}), 400

    # Hardcoded values
    level_id = 1

    # Generate the current timestamp
    timestamp = datetime.utcnow().isoformat()


    doc_ref = db.collection(colc).document(document_name)

    # Create the update data
    update_data = {
        "Level_ID": level_id,
        "Time": time,
        "TimeStamp": timestamp
    }

    try:
        # Try to update the document
        doc_ref.update(update_data)
        return jsonify({"message": "Record updated"}), 200
    except firestore.NotFound:
        # If the document does not exist, set it with the new data
        doc_ref.set(update_data)
        return jsonify({"message": "Record created"}), 201


if __name__ == '__main__':
    app.run(debug=True)
