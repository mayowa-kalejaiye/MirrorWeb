from flask import Flask, send_from_directory, request, jsonify
import os
import requests
from bs4 import BeautifulSoup
from flask_cors import CORS, cross_origin
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis
from werkzeug.middleware.proxy_fix import ProxyFix  # For production deployment behind a proxy




# Configure logging
logging.basicConfig(
    filename='clone.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Add ProxyFix middleware
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

# Initialize Redis for rate limiting
redis_connection = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri='redis://localhost:6379',
    default_limits=["10 per minute"]
)

# Directory for saving downloaded files
DOWNLOAD_FOLDER = 'cloned_site'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Middleware to handle reverse proxy setups (e.g., Nginx)
app.wsgi_app = ProxyFix(app.wsgi_app)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/about')
def me():
    return send_from_directory('.', 'me.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename)

@app.route('/screenshot', methods=['GET'])
@cross_origin(origins='https://mayowa-kalejaiye.github.io/MirrorWeb/')
@limiter.limit("10 per minute")
def screenshot():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL parameter is required"}), 400

    try:
        response = requests.get(url, timeout=10)  # Set a timeout to avoid hanging
        if response.status_code != 200:
            logging.error(f"Failed to fetch the URL: {url} with status code {response.status_code}")
            return jsonify({"error": "Failed to fetch the URL"}), 500

        soup = BeautifulSoup(response.text, 'html.parser')
        
        html_file_path = os.path.join(DOWNLOAD_FOLDER, 'index.html')
        with open(html_file_path, 'w', encoding='utf-8') as file:
            file.write(soup.prettify())

        # Extract and save CSS files
        css_files = soup.find_all('link', rel='stylesheet')
        for css in css_files:
            css_url = css.get('href')
            if css_url:
                if not css_url.startswith('http'):
                    css_url = requests.compat.urljoin(url, css_url)
                css_response = requests.get(css_url, timeout=10)
                if css_response.status_code == 200:
                    css_file_path = os.path.join(DOWNLOAD_FOLDER, css_url.split('/')[-1])
                    with open(css_file_path, 'w', encoding='utf-8') as file:
                        file.write(css_response.text)

        # Extract and save JavaScript files
        js_files = soup.find_all('script', src=True)
        for js in js_files:
            js_url = js.get('src')
            if js_url:
                if not js_url.startswith('http'):
                    js_url = requests.compat.urljoin(url, js_url)
                js_response = requests.get(js_url, timeout=10)
                if js_response.status_code == 200:
                    js_file_path = os.path.join(DOWNLOAD_FOLDER, js_url.split('/')[-1])
                    with open(js_file_path, 'w', encoding='utf-8') as file:
                        file.write(js_response.text)

        logging.info(f"Page downloaded successfully: {url}")
        return jsonify({"message": "Page downloaded successfully", "url": url}), 200
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching URL: {url} - {str(e)}")
        return jsonify({"error": "Error fetching URL: " + str(e)}), 500
    except Exception as e:
        logging.error(f"Unexpected error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Use a production server like Gunicorn instead of the built-in development server
    app.run(debug=True, use_reloader=False)
