import uuid
from langchain_core.messages import HumanMessage
from backend.app.graph import create_agent_graph
from backend.app.tools.booking import booking_service

def test_full_interleaving_dialogue():
    print("\n========== STARTING TEST: SECTION 7 INTERLEAVING DIALOGUE ==========\n")
    booking_service.reset()
    # Fresh graph with in-memory checkpointer for test isolation
    app = create_agent_graph(use_sqlite=False)
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}

    # Turn 1
    print(">>> TURN 1")
    t1_input = "Hi, I need to book a 1-on-1 Performance Review session."
    print(f"User: {t1_input}")
    res1 = app.invoke({"messages": [HumanMessage(content=t1_input)]}, config=config)
    last_msg1 = res1["messages"][-1].content
    print(f"Agent ({res1['active_node']}): {last_msg1}\n")
    assert "name and email" in last_msg1.lower(), "Turn 1 should ask for name and email"
    assert res1["booking_context"]["stage"] == "collecting_details"

    # Turn 2: Context Interleaving
    print(">>> TURN 2 (Interleaving FAQ mid-booking)")
    t2_input = "Alex Chen (alex.chen@example.com). Wait, before that, how often are performance reviews conducted according to the handbook?"
    print(f"User: {t2_input}")
    res2 = app.invoke({"messages": [HumanMessage(content=t2_input)]}, config=config)
    last_msg2 = res2["messages"][-1].content
    print(f"Agent ({res2['active_node']}): {last_msg2}\n")
    assert "citing page 4" in last_msg2.lower(), "Turn 2 must cite Page 4 from Employee Handbook"
    assert "returning to your booking" in last_msg2.lower(), "Turn 2 must resume booking"
    assert res2["booking_context"]["name"] == "Alex Chen", "Name must be preserved"
    assert res2["booking_context"]["email"] == "alex.chen@example.com", "Email must be preserved"

    # Turn 3: Final confirmation
    print(">>> TURN 3 (Slot confirmation)")
    t3_input = "Let's go with Friday at 10:30 AM."
    print(f"User: {t3_input}")
    res3 = app.invoke({"messages": [HumanMessage(content=t3_input)]}, config=config)
    last_msg3 = res3["messages"][-1].content
    print(f"Agent ({res3['active_node']}): {last_msg3}\n")
    assert "confirmed" in last_msg3.lower(), "Turn 3 must confirm booking"
    assert "#REV-" in last_msg3, "Turn 3 must include reference ID"
    assert res3["booking_context"]["confirmed"] is True, "Booking must be marked confirmed"

    print("========== ALL 3 TURNS PASSED WITH 100% SUCCESS! ==========\n")

if __name__ == "__main__":
    test_full_interleaving_dialogue()
