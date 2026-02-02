"""
Simple API test script
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health Check: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.status_code == 200

def test_list_meetings():
    """Test list meetings endpoint"""
    response = requests.get(f"{BASE_URL}/api/meetings/")
    print(f"\nList Meetings: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.status_code == 200

def test_create_meeting():
    """Test create meeting endpoint"""
    data = {
        "title": "Test Meeting",
        "participants": ["John Doe", "Jane Smith"]
    }
    response = requests.post(f"{BASE_URL}/api/meetings/", json=data)
    print(f"\nCreate Meeting: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    return response.status_code == 201

if __name__ == "__main__":
    print("🧪 Testing ASR Middleware API\n")
    print("=" * 50)
    
    try:
        # Test health
        if test_health():
            print("✅ Health check passed")
        else:
            print("❌ Health check failed")
        
        # Test list meetings
        if test_list_meetings():
            print("✅ List meetings passed")
        else:
            print("❌ List meetings failed")
        
        # Test create meeting
        if test_create_meeting():
            print("✅ Create meeting passed")
        else:
            print("❌ Create meeting failed")
        
        # List again to see the created meeting
        print("\n" + "=" * 50)
        print("📋 Meetings after creation:")
        test_list_meetings()
        
        print("\n✅ All tests completed!")
        print("\n📚 Access API docs at: http://localhost:8000/docs")
        
    except requests.exceptions.ConnectionError:
        print("❌ Error: Server is not running!")
        print("Start the server with: uv run python run.py")
