import pytest
from clone import app  # Import the Flask app

# Create a test client using the Flask app
@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index(client):
    """Test the index route."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'<!DOCTYPE html>' in response.data  # Check for some HTML content

def test_me(client):
    """Test the about page route."""
    response = client.get('/about')
    assert response.status_code == 200
    assert b'<title>About Me</title>' in response.data  # Check for specific content

def test_screenshot(client):
    """Test the screenshot route with a valid URL."""
    response = client.get('/screenshot?url=https://example.com')
    assert response.status_code == 200
    assert b'Page downloaded successfully' in response.data

def test_screenshot_no_url(client):
    """Test the screenshot route without providing a URL."""
    response = client.get('/screenshot')
    assert response.status_code == 400
    assert b'URL parameter is required' in response.data

def test_screenshot_invalid_url(client):
    """Test the screenshot route with an invalid URL."""
    response = client.get('/screenshot?url=https://invalid-url')
    assert response.status_code == 500
    assert b'Error fetching URL:' in response.data
