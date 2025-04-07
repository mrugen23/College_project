import os
from dotenv import load_dotenv
import pymysql
import jwt

# Load environment variables
load_dotenv()

# Database configuration
db_config = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'db': os.getenv('DB_NAME', 'finance_tracker'),
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

# JWT configuration
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key')

def get_db_connection():
    return pymysql.connect(**db_config)

def verify_token(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except:
        return None 