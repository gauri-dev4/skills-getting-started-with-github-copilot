from urllib.parse import quote
from uuid import uuid4

from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)


def _remove_email(email: str):
    """Helper to remove a test email from any activity participants list."""
    for act in activities.values():
        if email in act["participants"]:
            act["participants"].remove(email)


def test_get_activities():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    # Basic sanity: at least one known activity exists
    assert "Chess Club" in data


def test_signup_success_and_cleanup():
    activity = "Art Club"
    activity_enc = quote(activity, safe="")
    email = f"test+{uuid4().hex}@example.com"

    try:
        resp = client.post(f"/activities/{activity_enc}/signup", params={"email": email})
        assert resp.status_code == 200
        body = resp.json()
        assert "Signed up" in body.get("message", "")

        # Verify the participant was actually added to the in-memory store
        assert email in activities[activity]["participants"]
    finally:
        # cleanup
        _remove_email(email)


def test_signup_duplicate_fails():
    activity = "Programming Class"
    activity_enc = quote(activity, safe="")
    email = f"dup+{uuid4().hex}@example.com"

    try:
        # First signup should succeed
        resp1 = client.post(f"/activities/{activity_enc}/signup", params={"email": email})
        assert resp1.status_code == 200

        # Second signup should fail with 400
        resp2 = client.post(f"/activities/{activity_enc}/signup", params={"email": email})
        assert resp2.status_code == 400
        assert resp2.json().get("detail") == "Student already signed up for this activity"
    finally:
        _remove_email(email)


def test_signup_nonexistent_activity():
    activity = "No Such Club"
    activity_enc = quote(activity, safe="")
    email = f"noexist+{uuid4().hex}@example.com"

    resp = client.post(f"/activities/{activity_enc}/signup", params={"email": email})
    assert resp.status_code == 404
    assert resp.json().get("detail") == "Activity not found"


def test_unregister_success_and_cleanup():
    activity = "Soccer Team"
    activity_enc = quote(activity, safe="")
    email = f"toremove+{uuid4().hex}@example.com"

    try:
        # sign up first
        r1 = client.post(f"/activities/{activity_enc}/signup", params={"email": email})
        assert r1.status_code == 200

        # now unregister
        r2 = client.delete(f"/activities/{activity_enc}/participants", params={"email": email})
        assert r2.status_code == 200
        assert "Unregistered" in r2.json().get("message", "")

        # verify removed
        assert email not in activities[activity]["participants"]
    finally:
        # cleanup in case something failed
        if email in activities[activity]["participants"]:
            activities[activity]["participants"].remove(email)


def test_unregister_nonexistent_participant():
    activity = "Chess Club"
    activity_enc = quote(activity, safe="")
    email = f"notthere+{uuid4().hex}@example.com"

    resp = client.delete(f"/activities/{activity_enc}/participants", params={"email": email})
    assert resp.status_code == 404
    assert resp.json().get("detail") == "Participant not found"


def test_unregister_nonexistent_activity():
    activity = "No Club"
    activity_enc = quote(activity, safe="")
    email = f"noact+{uuid4().hex}@example.com"

    resp = client.delete(f"/activities/{activity_enc}/participants", params={"email": email})
    assert resp.status_code == 404
    assert resp.json().get("detail") == "Activity not found"
