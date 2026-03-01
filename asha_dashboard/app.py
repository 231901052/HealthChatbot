from flask import Flask, render_template, request, jsonify
import json
import os
import logging
logging.basicConfig(level=logging.INFO)
app = Flask(__name__, template_folder='.')

# This file will act as our temporary database for alerts
ALERTS_FILE = 'alerts.json'

def load_alerts():
    if os.path.exists(ALERTS_FILE):
        with open(ALERTS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_alerts(alerts):
    with open(ALERTS_FILE, 'w') as f:
        json.dump(alerts, f, indent=4)

@app.route('/')
def dashboard():
    alerts = load_alerts()
    return render_template('dashboard.html', alerts=alerts)

@app.route('/alert', methods=['POST'])
def receive_alert():
    try:
        data = request.json
        required_fields = ['phone', 'message', 'intent']
        if not all(field in data for field in required_fields):
            return jsonify({'status': 'error', 'message': 'Missing required fields'}), 400
        
        alerts = load_alerts()
        data['status'] = 'pending'
        
        alerts.append(data)
        print(f"SAVEDDDDD {alerts}")
        save_alerts(alerts)
        
        return jsonify({'status': 'success', 'message': 'Alert received successfully'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)