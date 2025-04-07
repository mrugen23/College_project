import requests

def test_groups_api():
    # Login to get token
    login_url = 'http://localhost:5002/api/auth/login'
    login_data = {
        'email': 'test2@example.com',
        'password': 'password123'
    }
    
    try:
        login_response = requests.post(login_url, json=login_data)
        print(f'Login response status: {login_response.status_code}')
        print(f'Login response: {login_response.text}')
        
        if login_response.status_code == 200:
            token = login_response.json().get('token')
            if token:
                print('Token obtained successfully')
                
                # Test GET /api/groups/
                groups_url = 'http://localhost:5002/api/groups/'
                headers = {'Authorization': token}
                
                groups_response = requests.get(groups_url, headers=headers)
                print(f'\nGroups API GET response status: {groups_response.status_code}')
                print(f'Groups API GET response: {groups_response.text}')
                
                # Test POST /api/groups/
                create_group_data = {
                    'name': 'Test Group',
                    'members': ['friend1@example.com', 'friend2@example.com']
                }
                
                create_response = requests.post(groups_url, json=create_group_data, headers=headers)
                print(f'\nCreate Group API response status: {create_response.status_code}')
                print(f'Create Group API response: {create_response.text}')
            else:
                print('No token in response')
        else:
            print('Login failed')
    
    except Exception as e:
        print(f'Error: {e}')

if __name__ == '__main__':
    test_groups_api() 