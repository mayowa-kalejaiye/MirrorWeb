from flask import Flask, render_template, send_from_directory, request, jsonify
import os
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# Directory for saving downloaded files
DOWNLOAD_FOLDER = 'cloned_site'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')  # This serves from the templates folder

@app.route('/me')
def me():
    return render_template('me.html')  # This serves from the templates folder

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(DOWNLOAD_FOLDER, filename)

@app.route('/screenshot', methods=['GET'])
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
