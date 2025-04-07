from config import get_db_connection

def check_tables():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check what tables exist
        cursor.execute('SHOW TABLES')
        tables = cursor.fetchall()
        print('Database Tables:')
        for table in tables:
            print(table)
            
        # Check virtual_members table
        try:
            cursor.execute('DESCRIBE virtual_members')
            vm_structure = cursor.fetchall()
            print('\nVirtual Members Table Structure:')
            for row in vm_structure:
                print(row)
        except Exception as e:
            print(f'\nError with virtual_members table: {e}')
            
        # Check group_members table
        try:
            cursor.execute('DESCRIBE group_members')
            gm_structure = cursor.fetchall()
            print('\nGroup Members Table Structure:')
            for row in gm_structure:
                print(row)
        except Exception as e:
            print(f'\nError with group_members table: {e}')
            
    except Exception as e:
        print(f'Database connection error: {e}')
    finally:
        conn.close()

if __name__ == '__main__':
    check_tables() 