# Wealth nest - Your personal Expense Management System

A full-stack web application for managing personal and group expenses, built with Flask and MySQL.

## Tech Stack

### Frontend
- HTML5
- CSS3
- Vanilla JavaScript
- Responsive Design

### Backend
- Python 3
- Flask Framework
- MySQL Database
- JWT Authentication

## Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.x
- MySQL Server
- pip (Python package manager)

## Features

- User Authentication (Register/Login)
- Personal Expense Tracking
- Budget Management
- Group Expense Management
- Expense Splitting
- Profile Management
- Responsive Design

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd <repository-name>
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r Backend/requirements.txt
   ```

4. **Set up MySQL Database**
   - Create a new MySQL database
   - Import the schema:
     ```bash
     mysql -u your_username -p your_database_name < Backend/schema.sql
     ```

5. **Configure Environment Variables**
   Create a `.env` file in the Backend directory with:
   ```
   DB_USER=your_mysql_username
   DB_PASSWORD=your_mysql_password
   DB_NAME=your_database_name
   SECRET_KEY=your_secret_key
   ```

## Required Python Packages

Install these packages using pip:
```bash
pip install flask
pip install flask-cors
pip install pymysql
pip install python-dotenv
pip install bcrypt
pip install PyJWT
pip install mysql-connector-python
```

## Running the Application

1. **Start the Flask Server**
   ```bash
   python3 -m Backend.app
   ```

2. **Access the Application**
   Open your web browser and navigate to:
   ```
   http://localhost:5002
   ```

## Project Structure

```
├── Backend/
│   ├── app.py              # Main application file
│   ├── config.py           # Configuration settings
│   ├── requirements.txt    # Python dependencies
│   ├── schema.sql         # Database schema
│   ├── migration.sql      # Database migrations
│   └── routes/
│       ├── auth.py        # Authentication routes
│       ├── finance.py     # Financial operations
│       └── groups.py      # Group management
│
└── frontend/
    ├── index.html         # Entry point
    ├── login.html         # Login page
    ├── register.html      # Registration page
    ├── home.html          # Dashboard
    ├── expenses.html      # Expense management
    ├── budgets.html       # Budget management
    ├── groups.html        # Group management
    ├── profile.html       # User profile
    ├── common.css         # Shared styles
    ├── navbar.js          # Navigation component
    └── footer.js          # Footer component
```

## API Endpoints

### Authentication
- POST `/api/auth/register` - Register new user
- POST `/api/auth/login` - User login
- GET `/api/auth/profile` - Get user profile
- POST `/api/auth/update-password` - Update password
- DELETE `/api/auth/delete-account` - Delete account

### Finance
- GET `/api/finance/budgets` - List budgets
- POST `/api/finance/budgets` - Create budget
- PUT `/api/finance/budgets/<id>` - Update budget
- DELETE `/api/finance/budgets/<id>` - Delete budget
- GET `/api/finance/expenses` - List expenses
- POST `/api/finance/expenses` - Create expense
- PUT `/api/finance/expenses/<id>` - Update expense
- DELETE `/api/finance/expenses/<id>` - Delete expense

### Groups
- GET `/api/groups` - List groups
- POST `/api/groups` - Create group
- GET `/api/groups/<id>` - Get group details
- DELETE `/api/groups/<id>` - Delete group
- POST `/api/groups/<id>/expenses` - Add group expense
- GET `/api/groups/<id>/expenses` - List group expenses

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
