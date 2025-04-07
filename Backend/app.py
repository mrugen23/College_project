from flask import Flask, send_from_directory, redirect
from flask_cors import CORS
import os

app = Flask(__name__, static_folder='../frontend')
CORS(app)

# Import blueprints
from Backend.routes.auth import auth_bp
from Backend.routes.finance import finance_bp
from Backend.routes.groups import groups_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(finance_bp, url_prefix='/api/finance')
app.register_blueprint(groups_bp, url_prefix='/api/groups')

# Serve frontend files
@app.route('/')
def index():
    return redirect('/login.html')

@app.route('/<path:path>')
def serve_frontend(path):
    return send_from_directory(app.static_folder, path)

# Health check endpoint
@app.route('/api/health', methods=['GET'])
def health_check():
    return {'status': 'healthy'}

if __name__ == '__main__':
    app.run(debug=True, port=5002) 