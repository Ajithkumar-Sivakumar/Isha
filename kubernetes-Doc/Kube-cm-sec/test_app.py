from app import app


def test_home_route():
    # Create a test client that simulates browser requests to the Flask app.
    client = app.test_client()
    # Send a GET request to the home page.
    response = client.get("/")
    # Assert that the response is successful.
    assert response.status_code == 200
    # Assert that the page contains the address-book heading.
    assert b"MY ADDRESS BOOK" in response.data


def test_health_route():
    # Create a test client for the Flask app.
    client = app.test_client()
    # Send a GET request to the health endpoint.
    response = client.get("/health")
    # Assert that the health check returns a successful status code.
    assert response.status_code == 200
    # Assert that the endpoint returns the expected health response.
    assert response.data == b"OK"
