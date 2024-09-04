from flask import Flask, send_from_directory, request, jsonify
import os
import requests
from bs4 import BeautifulSoup
from flask_cors import CORS, cross_origin
import logging
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import redis

logging.basicConfig(filename='clone.log', level=logging.DEBUG)

app = Flask(__name__)
CORS(app)

logging.basicConfig(
    filename='clone.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Test logging
# logging.debug('This is a debug message')
# logging.info('This is an info message')
# logging.error('This is an error message')


# Configure Redis as the storage backend
redis_connection = redis.Redis(host='localhost', port=6379, db=0)
limiter = Limiter(
    get_remote_address,
    app=app,
    storage_uri='redis://localhost:6379'
)

# Directory for saving downloaded files
DOWNLOAD_FOLDER = 'cloned_site'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

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
@cross_origin(origins='https://mayowa-kalejaiye.github.io/MirrorWeb/')  # Allow CORS for specific origin
@limiter.limit("10 per minute")  # Rate limit configuration
def screenshot():
    url = request.args.get('url')
    if not url:
        return jsonify({"error": "URL parameter is required"}), 400

    # Process URL and save files
    try:
        # Fetch the URL
        response = requests.get(url)
        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch the URL"}), 500

        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Save the HTML
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
                css_response = requests.get(css_url)
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
                js_response = requests.get(js_url)
                if js_response.status_code == 200:
                    js_file_path = os.path.join(DOWNLOAD_FOLDER, js_url.split('/')[-1])
                    with open(js_file_path, 'w', encoding='utf-8') as file:
                        file.write(js_response.text)

        return jsonify({"message": "Page downloaded successfully", "url": url}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
