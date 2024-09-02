from flask import Flask, request, send_from_directory, redirect, url_for
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

app = Flask(__name__)

CLONE_FOLDER = 'cloned_site'
app.config['CLONE_FOLDER'] = CLONE_FOLDER

def download_file(url, folder):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            parsed_url = urlparse(url)
            subdir = os.path.join(folder, os.path.dirname(parsed_url.path.lstrip('/')))
            os.makedirs(subdir, exist_ok=True)
            filepath = os.path.join(subdir, os.path.basename(parsed_url.path))
            
            with open(filepath, 'wb') as file:
                file.write(response.content)
            print(f"Downloaded: {url}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download {url}: {e}")

def clone_website(base_url, folder_name):
    try:
        response = requests.get(base_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        for tag, attr in [('link', 'href'), ('script', 'src'), ('img', 'src')]:
            for element in soup.find_all(tag):
                url = element.get(attr)
                if url:
                    full_url = urljoin(base_url, url)
                    element[attr] = f"/cloned_site/{os.path.basename(url)}"
                    download_file(full_url, folder_name)
        
        with open(os.path.join(folder_name, 'index.html'), 'w', encoding='utf-8') as file:
            file.write(soup.prettify())
    
    except requests.exceptions.RequestException as e:
        print(f"Failed to clone the website: {e}")

@app.route('/')
def home():
    return send_from_directory('.', 'index.html')

# @app.route('/about')
# def about():
#     return send_from_directory('.', 'me.html')

@app.route('/clone', methods=['POST'])
def clone_site():
    website_url = request.form['url']
    clone_website(website_url, app.config['CLONE_FOLDER'])
    return redirect(url_for('serve_cloned_site'))

@app.route('/cloned_site/')
def serve_cloned_site():
    return send_from_directory(app.config['CLONE_FOLDER'], 'index.html')

@app.route('/cloned_site/<path:filename>')
def serve_cloned_site_file(filename):
    return send_from_directory(app.config['CLONE_FOLDER'], filename)

if __name__ == '__main__':
    os.makedirs(CLONE_FOLDER, exist_ok=True)
    app.run(debug=True)
