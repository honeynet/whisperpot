from flask import Flask, render_template_string, request, redirect, url_for
import logging
import json
import time
import requests
from elasticsearch import Elasticsearch
import os
from dotenv import load_dotenv

app = Flask(__name__)

# Configure logging
logging.basicConfig(filename='honeypot.log', level=logging.WARNING)

CACHE_FILE = "ip_cache.json"

# Read the credentials from the environment variables
es_host = os.getenv('ES_HOST')
es_port = os.getenv('ES_PORT')
es_scheme = os.getenv('ES_SCHEME')
es_user = os.getenv('ES_USER')
es_password = os.getenv('ES_PASSWORD')

# Connect to the Elasticsearch instance using the credentials from the .env file
es = Elasticsearch([{'host': es_host, 'port': es_port, 'scheme': es_scheme}], http_auth=(es_user, es_password))

try:
    with open(CACHE_FILE, 'r') as f:
        ip_cache = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    ip_cache = {}

def get_ip_details(ip_address):
    # Check cache first
    if ip_address in ip_cache:
        return ip_cache[ip_address]

    # If not in cache, query the API
    url = f"http://ip-api.com/json/{ip_address}"
    response = requests.get(url)
    if response.status_code == 200:
        ip_details = response.json()
        ip_cache[ip_address] = ip_details  # Store the result in the cache

        # Save the updated cache to the file
        with open(CACHE_FILE, 'w') as f:
            json.dump(ip_cache, f)

        return ip_details
    else:
        return {}

def send_to_elasticsearch(log_data):
    index_name = "http_data"  # Name of the index

    # Index the data
    response = es.index(index=index_name, document=log_data)
    return response

def log_request(req, route_name):
    log_data = {
        "remoteaddr": req.remote_addr,
        "method": req.method,
        "requesturi": req.path,
        "headers": dict(req.headers),
        "UserAgent": req.user_agent.string,
        "form": req.form.to_dict(),
        "args": req.args.to_dict(),
        "data": req.data.decode('utf-8'),
        "eventtime": int(time.time()),
        "honeypotname": route_name
    }
    logging.warning(req)
    source_ip_details = get_ip_details(req.remote_addr)
    log_data["Source_IP_Details"] = source_ip_details
    # Send the data to Elasticsearch
    try:
        pass # response = send_to_elasticsearch(log_data)
    except Exception as e:
        # Log the error and the raw data
        logging.error(f"Failed to index document due to error: {str(e)}. Raw data: {log_data}")

    logging.warning(json.dumps(log_data))

@app.route('/')
def index():
    log_request(request, "Index Page Honeypot")
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>SIP Login</title>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    </head>
    <body>
        <div class="container mt-5">
            <h1 class="text-primary">MyCompany</h1>
            <h2>SIP Login</h2>
            <form action="/login" method="post">
                <div class="form-group">
                    <label for="username">Username:</label>
                    <input type="text" class="form-control" id="username" name="username">
                </div>
                <div class="form-group">
                    <label for="password">Password:</label>
                    <input type="password" class="form-control" id="password" name="password">
                </div>
                <input type="submit" class="btn btn-primary" value="Login">
            </form>
            <p><a href="/signup">Sign up</a></p>
        </div>
    </body>
    </html>
    ''')

@app.route('/signup', methods=['GET'])
def signup():
    log_request(request, "Signup Page Honeypot")
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sign Up</title>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    </head>
    <body>
        <div class="container mt-5">
            <h1 class="text-primary">MyCompany</h1>
            <h2>Sign Up</h2>
            <form action="/verify" method="post">
                <div class="form-group">
                    <label for="username">Username:</label>
                    <input type="text" class="form-control" id="username" name="username">
                </div>
                <div class="form-group">
                    <label for="email">Email:</label>
                    <input type="email" class="form-control" id="email" name="email">
                </div>
                <div class="form-group">
                    <label for="password">Password:</label>
                    <input type="password" class="form-control" id="password" name="password">
                </div>
                <div class="form-group">
                    <label for="confirm_password">Confirm Password:</label>
                    <input type="password" class="form-control" id="confirm_password" name="confirm_password">
                </div>
                <input type="submit" class="btn btn-primary" value="Sign Up">
            </form>
            <p class="mt-3">By signing up, you agree to our <a href="/terms">Terms and Conditions</a> and <a href="/privacy">Privacy Policy</a>.</p>
        </div>
    </body>
    </html>
    ''')

@app.route('/verify', methods=['POST'])
def verify():
    log_request(request, "Verify Page Honeypot")
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Verify Email</title>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    </head>
    <body>
        <div class="container mt-5">
            <h1 class="text-primary">MyCompany</h1>
            <h2>Verify Email</h2>
            <p>Thank you for signing up! Please check your email to verify your registration.</p>
        </div>
    </body>
    </html>
    ''')

@app.route('/login', methods=['POST'])
def login():
    log_request(request, "SIP Login Honeypot")
    return redirect(url_for('error'))

@app.route('/error', methods=['GET', 'POST'])
def error():
    log_request(request, "Error Page Honeypot")
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Error</title>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    </head>
    <body>
        <div class="container mt-5">
            <h1 class="text-primary">MyCompany</h1>
            <h2>Error</h2>
            <p>Invalid credentials. Please try again.</p>
        </div>
    </body>
    </html>
    ''')

@app.route('/terms', methods=['GET'])
def terms():
    log_request(request, "Terms Page Honeypot")
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Terms and Conditions</title>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    </head>
    <body>
        <div class="container mt-5">
            <h1 class="text-primary">MyCompany</h1>
            <h2>Terms and Conditions</h2>
            <p>These are the terms and conditions for using our service.</p>
            <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed euismod, nunc at bibendum tincidunt, ligula elit tincidunt sapien, nec bibendum elit elit eu elit. Sed euismod, nunc at bibendum tincidunt, ligula elit tincidunt sapien, nec bibendum elit elit eu elit.</p>
        </div>
    </body>
    </html>
    ''')

@app.route('/privacy', methods=['GET'])
def privacy():
    log_request(request, "Privacy Page Honeypot")
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Privacy Policy</title>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css">
    </head>
    <body>
        <div class="container mt-5">
            <h1 class="text-primary">MyCompany</h1>
            <h2>Privacy Policy</h2>
            <p>This is our privacy policy.</p>
            <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed euismod, nunc at bibendum tincidunt, ligula elit tincidunt sapien, nec bibendum elit elit eu elit. Sed euismod, nunc at bibendum tincidunt, ligula elit tincidunt sapien, nec bibendum elit elit eu elit.</p>
        </div>
    </body>
    </html>
    ''')

@app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'HEAD'])
def catch_all(path):
    log_request(request, "Catch All Honeypot")
    # Catch all other routes and show nothing
    return '', 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
