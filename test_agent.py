from support_agent.agent import answer_question, retrieve


def test_password_question_retrieves_password_article():
    articles = [{"id": "KB-1", "title": "Reset password", "content": "Use forgot password link", "keywords": ["login"]}]
    results = retrieve("I cannot login, reset password", articles)
    assert results and results[0]["id"] == "KB-1"


def test_answer_requires_human_approval_and_cites_sources():
    result = answer_question("How do I reset my password?")
    assert result["human_approval_required"] is True
    assert result["status"] == "draft_for_human_review"
    assert result["sources"]


def test_unknown_question_escalates():
    result = answer_question("Can you explain quantum entanglement?")
    assert "support specialist" in result["draft_reply"]
    assert not result["sources"]
