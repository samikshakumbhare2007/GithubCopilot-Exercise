"""
Tests for the Mergington High School Activities API
"""
import pytest


class TestGetActivities:
    """Test suite for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all registered activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_get_activities_includes_activity_details(self, client):
        """Test that activities include required fields"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity


class TestSignup:
    """Test suite for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]

    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant to the activity"""
        email = "newstudent@mergington.edu"
        client.post(f"/activities/Programming Class/signup?email={email}")
        
        response = client.get("/activities")
        activity = response.json()["Programming Class"]
        assert email in activity["participants"]

    def test_signup_duplicate_fails(self, client):
        """Test that signup fails when student is already registered"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_signup_nonexistent_activity_fails(self, client):
        """Test that signup fails for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_multiple_activities(self, client):
        """Test that same student can signup for multiple activities"""
        email = "versatile@mergington.edu"
        
        response1 = client.post(f"/activities/Chess Club/signup?email={email}")
        response2 = client.post(f"/activities/Programming Class/signup?email={email}")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        activities = client.get("/activities").json()
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]


class TestUnregister:
    """Test suite for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        email = "michael@mergington.edu"  # Already in Chess Club
        response = client.delete(
            f"/activities/Chess Club/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        # First signup
        email = "temp@mergington.edu"
        client.post(f"/activities/Drama Club/signup?email={email}")
        activities = client.get("/activities").json()
        assert email in activities["Drama Club"]["participants"]
        
        # Then unregister
        client.delete(f"/activities/Drama Club/unregister?email={email}")
        activities = client.get("/activities").json()
        assert email not in activities["Drama Club"]["participants"]

    def test_unregister_not_signed_up_fails(self, client):
        """Test that unregister fails if student is not signed up"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_unregister_nonexistent_activity_fails(self, client):
        """Test that unregister fails for non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_signup_after_unregister(self, client):
        """Test that student can re-signup after unregistering"""
        email = "reusable@mergington.edu"
        activity = "Basketball Team"
        
        # Signup
        response1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response1.status_code == 200
        
        # Unregister
        response2 = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response2.status_code == 200
        
        # Signup again
        response3 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response3.status_code == 200


class TestIntegration:
    """Integration tests for the full signup/management workflow"""

    def test_full_signup_workflow(self, client):
        """Test complete signup workflow"""
        email = "workflow@mergington.edu"
        activity = "Robotics Club"
        
        # Check initial state
        activities = client.get("/activities").json()
        initial_count = len(activities[activity]["participants"])
        
        # Signup
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify
        activities = client.get("/activities").json()
        assert len(activities[activity]["participants"]) == initial_count + 1
        assert email in activities[activity]["participants"]

    def test_activity_availability_updates(self, client):
        """Test that available spots are tracked correctly"""
        activity = "Tennis Club"
        initial_activities = client.get("/activities").json()
        initial_spots = (
            initial_activities[activity]["max_participants"] -
            len(initial_activities[activity]["participants"])
        )
        
        # Signup a new student
        client.post(f"/activities/{activity}/signup?email=tennis@mergington.edu")
        
        # Check spots decreased
        updated_activities = client.get("/activities").json()
        updated_spots = (
            updated_activities[activity]["max_participants"] -
            len(updated_activities[activity]["participants"])
        )
        
        assert updated_spots == initial_spots - 1
