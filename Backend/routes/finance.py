from flask import Blueprint, request, jsonify
from Backend.config import get_db_connection, verify_token

finance_bp = Blueprint('finance', __name__)

# Budget routes
@finance_bp.route('/budgets', methods=['POST'])
def create_budget():
    token = request.headers.get('Authorization')
    if not token or not verify_token(token):
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    user_id = verify_token(token)['user_id']
    category = data.get('category')
    amount = data.get('amount')
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    if not all([category, amount, start_date, end_date]):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                '''INSERT INTO budgets (user_id, category, amount, start_date, end_date)
                   VALUES (%s, %s, %s, %s, %s)''',
                (user_id, category, amount, start_date, end_date)
            )
            conn.commit()
            return jsonify({'message': 'Budget created successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@finance_bp.route('/budgets', methods=['GET'])
def get_budgets():
    token = request.headers.get('Authorization')
    if not token or not verify_token(token):
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = verify_token(token)['user_id']
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM budgets WHERE user_id = %s', (user_id,))
            budgets = cursor.fetchall()
            return jsonify(budgets)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@finance_bp.route('/budgets/<int:budget_id>', methods=['PUT'])
def update_budget(budget_id):
    token = request.headers.get('Authorization')
    if not token or not verify_token(token):
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    user_id = verify_token(token)['user_id']
    category = data.get('category')
    amount = data.get('amount')
    start_date = data.get('start_date')
    end_date = data.get('end_date')

    if not all([category, amount, start_date, end_date]):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Check if budget exists and belongs to user
            cursor.execute('SELECT id FROM budgets WHERE id = %s AND user_id = %s', (budget_id, user_id))
            if not cursor.fetchone():
                return jsonify({'error': 'Budget not found or no permission to update'}), 404
            
            # Update the budget
            cursor.execute(
                '''UPDATE budgets 
                   SET category = %s, amount = %s, start_date = %s, end_date = %s
                   WHERE id = %s''',
                (category, amount, start_date, end_date, budget_id)
            )
            conn.commit()
            return jsonify({'message': 'Budget updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@finance_bp.route('/budgets/<int:budget_id>', methods=['DELETE'])
def delete_budget(budget_id):
    token = request.headers.get('Authorization')
    if not token or not verify_token(token):
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = verify_token(token)['user_id']
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Check if budget exists and belongs to user
            cursor.execute('SELECT id FROM budgets WHERE id = %s AND user_id = %s', (budget_id, user_id))
            if not cursor.fetchone():
                return jsonify({'error': 'Budget not found or no permission to delete'}), 404
            
            # Delete the budget
            cursor.execute('DELETE FROM budgets WHERE id = %s', (budget_id,))
            conn.commit()
            return jsonify({'message': 'Budget deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# Expense routes
@finance_bp.route('/expenses', methods=['POST'])
def create_expense():
    token = request.headers.get('Authorization')
    if not token or not verify_token(token):
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    user_id = verify_token(token)['user_id']
    amount = data.get('amount')
    description = data.get('description')
    category = data.get('category')
    date = data.get('date')
    budget_id = data.get('budget_id')

    if not all([amount, description, category, date]):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # If budget_id is provided, verify it exists and belongs to the user
            if budget_id:
                cursor.execute('SELECT id FROM budgets WHERE id = %s AND user_id = %s', (budget_id, user_id))
                if not cursor.fetchone():
                    return jsonify({'error': 'Budget not found or no permission to link expense'}), 404

            cursor.execute(
                '''INSERT INTO expenses (user_id, amount, description, category, date, budget_id)
                   VALUES (%s, %s, %s, %s, %s, %s)''',
                (user_id, amount, description, category, date, budget_id)
            )
            conn.commit()
            return jsonify({'message': 'Expense created successfully'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@finance_bp.route('/expenses', methods=['GET'])
def get_expenses():
    token = request.headers.get('Authorization')
    if not token or not verify_token(token):
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = verify_token(token)['user_id']
    category = request.args.get('category')
    sort = request.args.get('sort', 'date_desc')
    date_range = request.args.get('date_range')
    budget_id = request.args.get('budget_id')

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            query = '''
                SELECT e.*, b.category as budget_name 
                FROM expenses e
                LEFT JOIN budgets b ON e.budget_id = b.id
                WHERE e.user_id = %s
            '''
            params = [user_id]

            # Add category filter if provided
            if category:
                query += ' AND e.category = %s'
                params.append(category)

            # Add budget filter if provided
            if budget_id:
                if budget_id == 'none':
                    query += ' AND e.budget_id IS NULL'
                else:
                    try:
                        # Make sure to convert string to integer
                        budget_id_int = int(budget_id)
                        query += ' AND e.budget_id = %s'
                        params.append(budget_id_int)
                        print(f"Filtering by budget_id: {budget_id_int}")
                    except ValueError:
                        print(f"Invalid budget_id format: {budget_id}")
                        return jsonify({'error': 'Invalid budget_id format'}), 400

            # Add date range filter if provided
            if date_range:
                if date_range == 'this_month':
                    query += ' AND DATE_FORMAT(e.date, "%Y-%m") = DATE_FORMAT(CURDATE(), "%Y-%m")'
                elif date_range == 'last_month':
                    query += ' AND DATE_FORMAT(e.date, "%Y-%m") = DATE_FORMAT(DATE_SUB(CURDATE(), INTERVAL 1 MONTH), "%Y-%m")'
                elif date_range == 'this_year':
                    query += ' AND YEAR(e.date) = YEAR(CURDATE())'

            # Add sorting
            if sort == 'date_asc':
                query += ' ORDER BY e.date ASC'
            elif sort == 'date_desc':
                query += ' ORDER BY e.date DESC'
            elif sort == 'amount_asc':
                query += ' ORDER BY e.amount ASC'
            elif sort == 'amount_desc':
                query += ' ORDER BY e.amount DESC'
            else:
                query += ' ORDER BY e.date DESC'
                
            # Print the query and parameters for debugging
            print(f"Executing query: {query}")
            print(f"With parameters: {params}")
            
            cursor.execute(query, params)
            expenses = cursor.fetchall()
            return jsonify(expenses)
    except Exception as e:
        print(f"Error in get_expenses: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@finance_bp.route('/expenses/<int:expense_id>', methods=['GET'])
def get_expense(expense_id):
    token = request.headers.get('Authorization')
    if not token or not verify_token(token):
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = verify_token(token)['user_id']
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                '''SELECT e.*, b.category as budget_name 
                   FROM expenses e
                   LEFT JOIN budgets b ON e.budget_id = b.id
                   WHERE e.id = %s AND e.user_id = %s''', 
                (expense_id, user_id)
            )
            expense = cursor.fetchone()
            
            if not expense:
                return jsonify({'error': 'Expense not found or no permission to view'}), 404
                
            return jsonify(expense)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@finance_bp.route('/expenses/<int:expense_id>', methods=['PUT'])
def update_expense(expense_id):
    token = request.headers.get('Authorization')
    if not token or not verify_token(token):
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    user_id = verify_token(token)['user_id']
    amount = data.get('amount')
    description = data.get('description')
    category = data.get('category')
    date = data.get('date')
    budget_id = data.get('budget_id')

    if not all([amount, description, category, date]):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Check if expense exists and belongs to user
            cursor.execute('SELECT id FROM expenses WHERE id = %s AND user_id = %s', (expense_id, user_id))
            if not cursor.fetchone():
                return jsonify({'error': 'Expense not found or no permission to update'}), 404
                
            # If budget_id is provided, verify it exists and belongs to the user
            if budget_id:
                cursor.execute('SELECT id FROM budgets WHERE id = %s AND user_id = %s', (budget_id, user_id))
                if not cursor.fetchone():
                    return jsonify({'error': 'Budget not found or no permission to link expense'}), 404
            
            # Update the expense
            cursor.execute(
                '''UPDATE expenses 
                   SET amount = %s, description = %s, category = %s, date = %s, budget_id = %s
                   WHERE id = %s''',
                (amount, description, category, date, budget_id, expense_id)
            )
            conn.commit()
            return jsonify({'message': 'Expense updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@finance_bp.route('/expenses/<int:expense_id>', methods=['DELETE'])
def delete_expense(expense_id):
    token = request.headers.get('Authorization')
    if not token or not verify_token(token):
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = verify_token(token)['user_id']
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Check if expense exists and belongs to user
            cursor.execute('SELECT id FROM expenses WHERE id = %s AND user_id = %s', (expense_id, user_id))
            if not cursor.fetchone():
                return jsonify({'error': 'Expense not found or no permission to delete'}), 404
            
            # Delete the expense
            cursor.execute('DELETE FROM expenses WHERE id = %s', (expense_id,))
            conn.commit()
            return jsonify({'message': 'Expense deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# Budget summary route
@finance_bp.route('/budgets/summary', methods=['GET'])
def get_budget_summary():
    token = request.headers.get('Authorization')
    if not token or not verify_token(token):
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = verify_token(token)['user_id']
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Get all active budgets with their total expenses
            query = '''
                SELECT 
                    b.id, 
                    b.category, 
                    b.amount as budget_amount, 
                    b.start_date, 
                    b.end_date,
                    COALESCE(SUM(e.amount), 0) as spent_amount,
                    (b.amount - COALESCE(SUM(e.amount), 0)) as remaining_amount,
                    CASE 
                        WHEN b.amount = 0 THEN 0 
                        ELSE ROUND((COALESCE(SUM(e.amount), 0) / b.amount) * 100, 2) 
                    END as percentage_used
                FROM 
                    budgets b
                LEFT JOIN 
                    expenses e ON b.id = e.budget_id AND e.date BETWEEN b.start_date AND b.end_date
                WHERE 
                    b.user_id = %s
                GROUP BY 
                    b.id
                ORDER BY 
                    percentage_used DESC
            '''
            cursor.execute(query, (user_id,))
            budget_summary = cursor.fetchall()
            
            # Get total unassigned expenses
            query = '''
                SELECT 
                    COALESCE(SUM(amount), 0) as unassigned_expenses
                FROM 
                    expenses 
                WHERE 
                    user_id = %s AND budget_id IS NULL
            '''
            cursor.execute(query, (user_id,))
            unassigned = cursor.fetchone()
            
            return jsonify({
                'budgets': budget_summary,
                'unassigned_expenses': unassigned['unassigned_expenses'] if unassigned else 0
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close() 