from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.tools.booking import booking_service

client = TestClient(app)

def setup_function():
    booking_service.reset()

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_slots_endpoint():
    response = client.get("/api/slots")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["available_slots"]) > 0

def test_chat_turn_flow():
    # Turn 1: Initiate booking
    res1 = client.post("/api/chat", json={"message": "Hi, I need to book a 1-on-1 Performance Review session."})
    assert res1.status_code == 200
    data1 = res1.json()
    thread_id = data1["thread_id"]
    assert thread_id is not None
    assert "name and email" in data1["reply"].lower()

    # Turn 2: Context Interleaving (FAQ mid-booking)
    res2 = client.post("/api/chat", json={
        "message": "Alex Chen (alex.chen@example.com). Wait, before that, how often are performance reviews conducted according to the handbook?",
        "thread_id": thread_id
    })
    assert res2.status_code == 200
    data2 = res2.json()
    assert "citing page 4" in data2["reply"].lower()
    assert "returning to your booking" in data2["reply"].lower()

    # Turn 3: Slot selection
    res3 = client.post("/api/chat", json={
        "message": "Let's go with Friday at 10:30 AM.",
        "thread_id": thread_id
    })
    assert res3.status_code == 200
    data3 = res3.json()
    assert "confirmed" in data3["reply"].lower()
    assert "#REV-" in data3["reply"]

    # Verify checkpointer state inspection endpoint
    res_state = client.get(f"/api/state/{thread_id}")
    assert res_state.status_code == 200
    state_data = res_state.json()
    assert state_data["exists"] is True
    assert state_data["booking_context"]["name"] == "Alex Chen"
    assert state_data["booking_context"]["confirmed"] is True

if __name__ == "__main__":
    booking_service.reset()
    test_health_endpoint()
    test_slots_endpoint()
    test_chat_turn_flow()
    print("All FastAPI Route Integration Tests Passed Successfully!")
