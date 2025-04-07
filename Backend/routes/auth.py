from flask import Blueprint, request, jsonify
from Backend.config import get_db_connection, SECRET_KEY, verify_token
import bcrypt
import jwt
from datetime import datetime, timedelta
from functools import wraps
import os

auth_bp = Blueprint('auth', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'No token provided'}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': 'Invalid token'}), 401
        
        return f(payload, *args, **kwargs)
    return decorated_function

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    if not all([username, email, password]):
        return jsonify({'error': 'Missing required fields'}), 400

    # Hash password
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Check if username or email already exists
            cursor.execute('SELECT id FROM users WHERE username = %s OR email = %s', (username, email))
            if cursor.fetchone():
                return jsonify({'error': 'Username or email already exists'}), 400

            # Insert new user
            cursor.execute(
                'INSERT INTO users (username, email, password) VALUES (%s, %s, %s)',
                (username, email, hashed_password)
            )
            conn.commit()
            user_id = cursor.lastrowid

        # Generate JWT token
        token = jwt.encode({
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(days=1)
        }, SECRET_KEY, algorithm='HS256')

        return jsonify({
            'message': 'User registered successfully',
            'token': token,
            'user_id': user_id
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not all([email, password]):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('SELECT id, password FROM users WHERE email = %s', (email,))
            user = cursor.fetchone()

            if not user or not bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
                return jsonify({'error': 'Invalid email or password'}), 401

            # Generate JWT token
            token = jwt.encode({
                'user_id': user['id'],
                'exp': datetime.utcnow() + timedelta(days=1)
            }, SECRET_KEY, algorithm='HS256')

            return jsonify({
                'message': 'Login successful',
                'token': token,
                'user_id': user['id']
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@auth_bp.route('/profile', methods=['GET'])
@login_required
def get_profile(payload):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('SELECT id, username, email FROM users WHERE id = %s', (payload['user_id'],))
            user = cursor.fetchone()
            
            if not user:
                return jsonify({'error': 'User not found'}), 404

            return jsonify({
                'id': user['id'],
                'username': user['username'],
                'email': user['email']
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@auth_bp.route('/update-password', methods=['POST'])
@login_required
def update_password(payload):
    data = request.get_json()
    current_password = data.get('currentPassword')
    new_password = data.get('newPassword')

    if not all([current_password, new_password]):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Verify current password
            cursor.execute('SELECT password FROM users WHERE id = %s', (payload['user_id'],))
            user = cursor.fetchone()

            if not user or not bcrypt.checkpw(current_password.encode('utf-8'), user['password'].encode('utf-8')):
                return jsonify({'error': 'Current password is incorrect'}), 401

            # Update password
            hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
            cursor.execute('UPDATE users SET password = %s WHERE id = %s', (hashed_password, payload['user_id']))
            conn.commit()

            return jsonify({'message': 'Password updated successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@auth_bp.route('/delete-account', methods=['DELETE'])
@login_required
def delete_account(payload):
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Delete user's data from related tables first
            cursor.execute('DELETE FROM expenses WHERE user_id = %s', (payload['user_id'],))
            cursor.execute('DELETE FROM budgets WHERE user_id = %s', (payload['user_id'],))
            cursor.execute('DELETE FROM group_members WHERE user_id = %s', (payload['user_id'],))
            cursor.execute('DELETE FROM group_expenses WHERE user_id = %s', (payload['user_id'],))
            
            # Delete the user
            cursor.execute('DELETE FROM users WHERE id = %s', (payload['user_id'],))
            conn.commit()

            return jsonify({'message': 'Account deleted successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@auth_bp.route('/upload-photo', methods=['POST'])
@login_required
def upload_photo(payload):
    """
    Endpoint to upload a profile photo
    Expects a file upload with name 'photo'
    Returns the URL of the uploaded photo
    """
    if 'photo' not in request.files:
        return jsonify({'error': 'No photo uploaded'}), 400
    
    photo = request.files['photo']
    
    if photo.filename == '':
        return jsonify({'error': 'No photo selected'}), 400
    
    if photo:
        try:
            # Check file type for security
            filename = photo.filename.lower()
            if not filename.endswith(('.png', '.jpg', '.jpeg', '.gif')):
                return jsonify({'error': 'Invalid file type. Only png, jpg, jpeg, and gif are allowed'}), 400
            
            # Generate a unique filename
            new_filename = f"user_{payload['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
            
            # Ensure the upload directory exists
            upload_path = os.path.join('frontend', 'uploads')
            if not os.path.exists(upload_path):
                os.makedirs(upload_path)
            
            # Save the photo
            file_path = os.path.join(upload_path, new_filename)
            photo.save(file_path)
            
            # Update the user's profile photo path in the database
            conn = get_db_connection()
            with conn.cursor() as cursor:
                cursor.execute('UPDATE users SET profile_photo = %s WHERE id = %s', 
                              (f'uploads/{new_filename}', payload['user_id']))
                conn.commit()
            
            return jsonify({
                'message': 'Photo uploaded successfully',
                'photo_url': f'uploads/{new_filename}'
            })
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        finally:
            if 'conn' in locals():
                conn.close()
    
    return jsonify({'error': 'Failed to upload photo'}), 500 