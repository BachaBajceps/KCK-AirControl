
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

# This will store the latest hand data
latest_hand_data = {"x": 0, "y": 0}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/hand_data', methods=['POST'])
def receive_hand_data():
    global latest_hand_data
    data = request.json
    if data and 'x' in data and 'y' in data:
        latest_hand_data = {"x": data['x'], "y": data['y']}
        print(f"Received hand data: X={latest_hand_data['x']}, Y={latest_hand_data['y']}")
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error", "message": "Invalid data"}), 400

@app.route('/get_hand_data', methods=['GET'])
def get_hand_data():
    return jsonify(latest_hand_data), 200

if __name__ == '__main__':
    # Run on 0.0.0.0 to be accessible from other devices on the network
    # Use one of the provided ports, e.g., 53102
    app.run(host='0.0.0.0', port=53102, debug=True)
