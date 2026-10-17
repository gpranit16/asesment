from backend.app.rag.retriever import retriever

def test_rag_performance_review():
    res = retriever.query("how often are performance reviews conducted according to the handbook?", top_k=3)
    assert len(res["sources"]) > 0, "Should return at least 1 source chunk"
    assert res["primary_page"] == 4, f"Expected Page 4 for performance review, got Page {res['primary_page']}"
    assert any(4 == s["page"] for s in res["sources"]), "Page 4 must be among the cited pages"
    assert "performance review" in res["context_text"].lower()

def test_rag_workplace_safety():
    res = retriever.query("What is the goal of workplace safety at Zava?", top_k=3)
    assert len(res["sources"]) > 0
    assert any("safety" in s["snippet"].lower() for s in res["sources"])

if __name__ == "__main__":
    test_rag_performance_review()
    test_rag_workplace_safety()
    print("All RAG Retriever Tests Passed Successfully!")
