import requests

# First test Flask directly (bypass ngrok)
LOCAL_URL = "http://localhost:5000"

print("🧪 Testing Flask Backend Directly (localhost)...")
print("=" * 50)

# Test 1: Local root endpoint
print("\n1️⃣ Testing local root endpoint...")
try:
    response = requests.get(f"{LOCAL_URL}/")
    print(f"✅ Status: {response.status_code}")
    print(f"✅ Response: {response.json()}")
except Exception as e:
    print(f"❌ Error: {e}")
    print("❌ Flask is NOT running! Start it with: python app.py")
    exit(1)

# Test 2: Generate token locally
print("\n2️⃣ Testing local token generation...")
try:
    response = requests.post(f"{LOCAL_URL}/generate_token")
    print(f"✅ Status: {response.status_code}")
    data = response.json()
    print(f"✅ Response: {data}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 3: Get QR code locally
print("\n3️⃣ Testing local QR retrieval...")
try:
    response = requests.get(f"{LOCAL_URL}/get_qr")
    print(f"✅ Status: {response.status_code}")
    print(f"✅ Content-Type: {response.headers.get('Content-Type')}")
    
    if response.status_code == 200:
        with open("local_test_qr.png", "wb") as f:
            f.write(response.content)
        print("✅ QR saved as 'local_test_qr.png'")
        print("\n🎉 Flask backend is working perfectly!")
    else:
        print(f"❌ Got status: {response.status_code}")
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 50)
print("\nIf Flask works locally but ngrok gives 400:")
print("💡 The issue is with ngrok configuration")
print("💡 Try updating ngrok or check ngrok dashboard")