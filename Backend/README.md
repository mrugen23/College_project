# Personal Finance Tracker Backend

This is the backend for a personal finance tracker application that helps users manage their budgets, track expenses, and split expenses in groups.

## Features

- User authentication (register/login)
- Budget management
- Expense tracking
- Group expense splitting
- Expense sharing among group members

## Prerequisites

- Python 3.8 or higher
- MySQL 5.7 or higher
- pip (Python package manager)

## Setup

1. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up MySQL:
   - Install MySQL if not already installed
   - Create a new database named `finance_tracker`
   - Update the `.env` file with your MySQL credentials

4. Initialize the database:
```bash
mysql -u your_username -p finance_tracker < schema.sql
```

5. Configure environment variables:
   - Copy `.env.example` to `.env`
   - Update the values in `.env` with your configuration

## Running the Application

1. Start the Flask server:
```bash
python app.py
```

The server will start on `http://localhost:5000`

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login user

### Budgets
- `POST /api/finance/budgets` - Create a new budget
- `GET /api/finance/budgets` - Get all budgets for the user

### Expenses
- `POST /api/finance/expenses` - Create a new expense
- `GET /api/finance/expenses` - Get all expenses for the user

### Groups
- `POST /api/groups/groups` - Create a new group
- `GET /api/groups/groups` - Get all groups for the user
- `POST /api/groups/groups/<group_id>/expenses` - Create a group expense
- `GET /api/groups/groups/<group_id>/expenses` - Get all expenses for a group

## Security

- All endpoints except `/api/auth/register` and `/api/auth/login` require a JWT token in the Authorization header
- Passwords are hashed using bcrypt
- JWT tokens expire after 24 hours

## Error Handling

The API returns appropriate HTTP status codes and error messages in JSON format:
- 200: Success
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 500: Internal Server Error

Example error response:
```json
{
    "error": "Error message here"
}
``` 