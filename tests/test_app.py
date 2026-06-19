from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


BASE_ACTIVITIES = deepcopy(app_module.activities)


def reset_activities() -> None:
    app_module.activities.clear()
    app_module.activities.update(deepcopy(BASE_ACTIVITIES))


@pytest.fixture(autouse=True)
def isolated_activities():
    reset_activities()
    yield
    reset_activities()


def test_get_activities_returns_all_activities():
    # Arrange
    client = TestClient(app_module.app)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert set(data) == set(BASE_ACTIVITIES)
    assert data["Chess Club"]["max_participants"] == 12


def test_root_redirects_to_static_index():
    # Arrange
    client = TestClient(app_module.app)

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_signup_for_activity_adds_participant():
    # Arrange
    client = TestClient(app_module.app)
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"
    initial_participants = list(app_module.activities[activity_name]["participants"])

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert app_module.activities[activity_name]["participants"] == initial_participants + [email]


def test_signup_rejects_duplicate_participant():
    # Arrange
    client = TestClient(app_module.app)
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    initial_participants = list(app_module.activities[activity_name]["participants"])

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}
    assert app_module.activities[activity_name]["participants"] == initial_participants


def test_signup_rejects_unknown_activity():
    # Arrange
    client = TestClient(app_module.app)

    # Act
    response = client.post(
        "/activities/Robotics Club/signup",
        params={"email": "new.student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_from_activity_removes_participant():
    # Arrange
    client = TestClient(app_module.app)
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in app_module.activities[activity_name]["participants"]


def test_unregister_rejects_missing_participant():
    # Arrange
    client = TestClient(app_module.app)
    activity_name = "Chess Club"
    email = "new.student@mergington.edu"
    initial_participants = list(app_module.activities[activity_name]["participants"])

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student is not signed up for this activity"}
    assert app_module.activities[activity_name]["participants"] == initial_participants


def test_unregister_rejects_unknown_activity():
    # Arrange
    client = TestClient(app_module.app)

    # Act
    response = client.delete(
        "/activities/Robotics Club/signup",
        params={"email": "new.student@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}