from config import get_db_connection

def check_users():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get all users 
        cursor.execute('SELECT id, username, email FROM users')
        users = cursor.fetchall()
        
        print('Users in the database:')
        for user in users:
            print(f"ID: {user['id']}, Username: {user['username']}, Email: {user['email']}")
            
    except Exception as e:
        print(f'Error: {e}')
    finally:
        conn.close()

if __name__ == '__main__':
    check_users() 