from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
import qrcode
import requests
import secrets
import time
from io import BytesIO
import os
ATTENDANCE_RECORDS = {}

app = Flask(__name__)

# Enable CORS for all routes with proper configuration
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "ngrok-skip-browser-warning"]
    }
})

CURRENT_TOKEN = None
TOKEN_EXPIRY = 0
QR_IMAGE_BUFFER = None
CURRENT_SUBJECT = None

# Auto-detect backend URL based on environment
def get_backend_url():
    if os.getenv('RENDER'):
        # On Render, construct URL from hostname
        hostname = os.getenv('RENDER_EXTERNAL_HOSTNAME')
        return f"https://{hostname}"
    elif os.getenv('BACKEND_URL'):
        # Use environment variable if set
        return os.getenv('BACKEND_URL')
    else:
        # Local development
        return "http://127.0.0.1:5050"

BACKEND_URL = get_backend_url()

APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbx6tZEaSMDB4gec-NzK2BqAdJH3MbbM9n2HNhNJv9wob8Uivf0E28y-nYrwp-Kc3zAH/exec"

def save_to_google_sheet(roll, name, subject, token):
    payload = {
        "roll": roll,
        "name": name,
        "subject": subject,
        "token": token
    }
    try:
        requests.post(APPS_SCRIPT_URL, json=payload, timeout=5)
    except Exception as e:
        print("Sheet error:", e)

@app.route("/")
def home():
    return jsonify({
        "message": "Backend is running!",
        "backend_url": BACKEND_URL
    })

@app.route("/config")
def get_config():
    """Provide backend URL to frontend"""
    return jsonify({"backend_url": BACKEND_URL})

@app.route("/teacher.html")
def teacher_page():
    """Serve teacher page from frontend folder"""
    try:
        with open('frontend/teacher.html', 'r', encoding='utf-8') as f:
            content = f.read()
            return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except FileNotFoundError:
        return f"teacher.html not found. Current dir: {os.getcwd()}", 404

@app.route("/student.html")
def student_page():
    """Serve student page from frontend folder"""
    try:
        print(f"📱 Student page requested with token: {request.args.get('token')}")
        with open('frontend/student.html', 'r', encoding='utf-8') as f:
            content = f.read()
            return content, 200, {'Content-Type': 'text/html; charset=utf-8'}
    except FileNotFoundError:
        print(f"❌ student.html not found!")
        return f"student.html not found. Current dir: {os.getcwd()}", 404

@app.route("/style.css")
def serve_css():
    """Serve CSS file from frontend folder"""
    try:
        with open('frontend/style.css', 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/css; charset=utf-8'}
    except FileNotFoundError:
        return "style.css not found", 404

@app.route("/script.js")
def serve_js():
    """Serve JavaScript file from frontend folder"""
    try:
        with open('frontend/script.js', 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'application/javascript; charset=utf-8'}
    except FileNotFoundError:
        return "script.js not found", 404

@app.route("/generate_token", methods=["GET", "POST", "OPTIONS"])
def generate_token():
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,ngrok-skip-browser-warning")
        response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        return response, 200
    
    global CURRENT_TOKEN, TOKEN_EXPIRY, QR_IMAGE_BUFFER, CURRENT_SUBJECT

    data = request.get_json() if request.is_json else {}
    subject = data.get("subject", "General")
    
    CURRENT_TOKEN = secrets.token_hex(4)
    TOKEN_EXPIRY = time.time() + 120
    CURRENT_SUBJECT = subject

    url = f"{BACKEND_URL}/attendance?token={CURRENT_TOKEN}"
    print(f"🔗 Generated QR URL: {url}")
    print(f"📚 Subject: {subject}")

    qr = qrcode.make(url)
    QR_IMAGE_BUFFER = BytesIO()
    qr.save(QR_IMAGE_BUFFER, format="PNG")
    QR_IMAGE_BUFFER.seek(0)

    response = jsonify({
        "status": "success",
        "token": CURRENT_TOKEN,
        "subject": subject,
        "expires_in": 120
    })
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response

@app.route("/get_qr", methods=["GET", "OPTIONS"])
def get_qr():
    if request.method == "OPTIONS":
        response = jsonify({"status": "ok"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,ngrok-skip-browser-warning")
        response.headers.add("Access-Control-Allow-Methods", "GET,OPTIONS")
        return response, 200
    
    if QR_IMAGE_BUFFER is None:
        return jsonify({"error": "QR not generated"}), 404

    QR_IMAGE_BUFFER.seek(0)
    return send_file(QR_IMAGE_BUFFER, mimetype="image/png")

# Track submissions per device
DEVICE_SUBMISSIONS = {}  # {device_id: [tokens_used]}

@app.route("/mark_attendance", methods=["POST"])
def mark_attendance():
    data = request.get_json()

    token = data.get("token")
    roll = data.get("roll")
    name = data.get("student_name")

    if not token or not roll or not name:
        return jsonify({
            "status": "error",
            "message": "Invalid data received ❌"
        }), 400

    # Initialize token records
    if token not in DEVICE_SUBMISSIONS:
        DEVICE_SUBMISSIONS[token] = set()

    if token not in ATTENDANCE_RECORDS:
        ATTENDANCE_RECORDS[token] = set()

    # Device ID (basic proxy prevention)
    device_id = request.remote_addr + request.headers.get("User-Agent", "")

    # Same device check
    if device_id in DEVICE_SUBMISSIONS[token]:
        return jsonify({
            "status": "error",
            "message": "Attendance already marked from this device ⚠️"
        })

    # Same roll check
    if roll in ATTENDANCE_RECORDS[token]:
        return jsonify({
            "status": "error",
            "message": "This roll number already marked attendance ⚠️"
        })

    DEVICE_SUBMISSIONS[token].add(device_id)
    ATTENDANCE_RECORDS[token].add(roll)

    save_to_google_sheet(roll, name, CURRENT_SUBJECT, token)

    return jsonify({
        "status": "success",
        "message": "Attendance marked successfully ✅"
    })

@app.route("/attendance", methods=["GET"])
def attendance_page():
    """Redirect to student page with token"""
    token = request.args.get("token")
    print(f"🎯 /attendance called with token: {token}")
    
    if not token:
        return "Token missing ❌", 400

    redirect_url = f"{BACKEND_URL}/student.html?token={token}"
    
    print(f"🔗 Redirecting to: {redirect_url}")
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <meta http-equiv="refresh" content="0; url={redirect_url}">
        <script>window.location.href = "{redirect_url}";</script>
        <title>Redirecting...</title>
    </head>
    <body style="font-family: Arial; text-align: center; padding: 50px;">
        <h2>🔄 Redirecting to attendance form...</h2>
        <p>If not redirected automatically, <a href="{redirect_url}">click here</a>.</p>
    </body>
    </html>
    '''

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🚀 ATTENDANCE SYSTEM STARTING")
    print("="*50)
    
    print(f"\n📁 Current directory: {os.getcwd()}")
    
    if os.path.exists('frontend'):
        print("✅ frontend folder found!")
        files = os.listdir('frontend')
        print(f"📄 Files in frontend: {files}")
    else:
        print("❌ WARNING: frontend folder NOT found!")
        print("Please create a 'frontend' folder and put your HTML/CSS/JS files there")
    
    print(f"\n🌐 Backend URL: {BACKEND_URL}")
    print(f"\n📱 Access URL: {BACKEND_URL}/teacher.html")
    print("\n" + "="*50 + "\n")
    
    # Use PORT environment variable for Render
    port = int(os.getenv('PORT', 5050))
    app.run(debug=False, port=port, host='0.0.0.0')