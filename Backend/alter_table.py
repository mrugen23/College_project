from config import get_db_connection

def alter_group_members_table():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Modify the user_id field to allow NULL values
        cursor.execute('''
            ALTER TABLE group_members 
            MODIFY COLUMN user_id INT NULL
        ''')
        
        conn.commit()
        print("Group members table updated: user_id can now be NULL")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    alter_group_members_table() 