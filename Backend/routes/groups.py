from flask import Blueprint, request, jsonify
from Backend.config import get_db_connection, verify_token
from datetime import datetime

groups_bp = Blueprint('groups', __name__)

# Group routes
@groups_bp.route('/', methods=['POST'])
def create_group():
    token = request.headers.get('Authorization')
    if not token or not verify_token(token):
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    user_id = verify_token(token)['user_id']
    name = data.get('name')
    members = data.get('members', [])

    if not name:
        return jsonify({'error': 'Group name is required'}), 400

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Create group
            cursor.execute(
                'INSERT INTO expense_groups (name, created_by) VALUES (%s, %s)',
                (name, user_id)
            )
            group_id = cursor.lastrowid

            # Add creator as member
            cursor.execute(
                'INSERT INTO group_members (group_id, user_id, virtual_member_id) VALUES (%s, %s, NULL)',
                (group_id, user_id)
            )

            # Add members by name
            for member_name in members:
                if member_name and member_name.strip():
                    # Create a virtual member with the provided name/email
                    cursor.execute(
                        'INSERT INTO virtual_members (name, created_by) VALUES (%s, %s)',
                        (member_name.strip(), user_id)
                    )
                    virtual_member_id = cursor.lastrowid
                    
                    # Add virtual member to the group - with NULL user_id
                    cursor.execute(
                        'INSERT INTO group_members (group_id, user_id, virtual_member_id) VALUES (%s, NULL, %s)',
                        (group_id, virtual_member_id)
                    )

            conn.commit()
            return jsonify({'message': 'Group created successfully', 'group_id': group_id}), 201
    except Exception as e:
        print(f"Error creating group: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@groups_bp.route('/', methods=['GET'])
def get_groups():
    token = request.headers.get('Authorization')
    if not token or not verify_token(token):
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = verify_token(token)['user_id']
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Get groups with correct member count (only counting virtual members)
            cursor.execute('''
                SELECT g.id, g.name, g.created_by, g.created_at,
                    (SELECT COUNT(*) FROM group_members WHERE group_id = g.id AND virtual_member_id IS NOT NULL) as virtual_member_count,
                    COALESCE((SELECT SUM(amount) FROM group_expenses WHERE group_id = g.id), 0) as total_expenses
                FROM expense_groups g
                WHERE g.id IN (
                    SELECT DISTINCT group_id FROM group_members WHERE user_id = %s
                ) OR g.created_by = %s
                GROUP BY g.id
            ''', (user_id, user_id))
            groups = cursor.fetchall()
            
            # Format response
            formatted_groups = []
            for group in groups:
                formatted_groups.append({
                    'id': group['id'],
                    'name': group['name'],
                    'created_by': group['created_by'],
                    'created_at': group['created_at'],
                    'member_count': group['virtual_member_count'],
                    'total_expenses': float(group['total_expenses']) if group['total_expenses'] else 0
                })
            
            return jsonify(formatted_groups)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@groups_bp.route('/<int:group_id>', methods=['GET'])
def get_group_details(group_id):
    token = request.headers.get('Authorization')
    if not token or not verify_token(token):
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = verify_token(token)['user_id']
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Verify user is group member or creator - FIXED QUERY
            cursor.execute(
                '''SELECT 1 FROM expense_groups g 
                   WHERE g.id = %s AND (
                       g.created_by = %s OR 
                       EXISTS (SELECT 1 FROM group_members gm WHERE gm.group_id = g.id AND gm.user_id = %s)
                   )''',
                (group_id, user_id, user_id)
            )
            
            group_exists = cursor.fetchone()
            if not group_exists:
                return jsonify({'error': 'Not authorized to view this group'}), 403

            # Get group details
            cursor.execute('SELECT * FROM expense_groups WHERE id = %s', (group_id,))
            group = cursor.fetchone()
            
            if not group:
                return jsonify({'error': 'Group not found'}), 404

            creator_id = group['created_by']
            
            # Get only the current user if they're a member (should be the creator)
            cursor.execute('''
                SELECT u.id, u.username, u.email, 'regular' as member_type
                FROM users u
                JOIN group_members gm ON u.id = gm.user_id
                WHERE gm.group_id = %s AND u.id = %s
            ''', (group_id, user_id))
            regular_members = cursor.fetchall()
            
            # Get virtual members for this group only 
            cursor.execute('''
                SELECT vm.id, vm.name as username, '' as email, 'virtual' as member_type
                FROM virtual_members vm
                JOIN group_members gm ON vm.id = gm.virtual_member_id
                WHERE gm.group_id = %s
                ORDER BY vm.id
            ''', (group_id,))
            virtual_members = cursor.fetchall()
            
            # Combine members
            all_members = regular_members + virtual_members
            
            # Get total expenses
            cursor.execute('SELECT SUM(amount) as total FROM group_expenses WHERE group_id = %s', (group_id,))
            total = cursor.fetchone()
            
            # Prepare response
            result = dict(group)
            result['members'] = all_members
            result['total_expenses'] = float(total['total']) if total and total['total'] else 0
            
            return jsonify(result)
    except Exception as e:
        print(f"Error in get_group_details: {str(e)}")  # Add debugging
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@groups_bp.route('/<int:group_id>', methods=['DELETE'])
def delete_group(group_id):
    token = request.headers.get('Authorization')
    if not token or not verify_token(token):
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = verify_token(token)['user_id']
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Verify user is the creator of the group
            cursor.execute(
                'SELECT created_by FROM expense_groups WHERE id = %s',
                (group_id,)
            )
            group = cursor.fetchone()
            
            if not group:
                return jsonify({'error': 'Group not found'}), 404
                
            if group['created_by'] != user_id:
                return jsonify({'error': 'Only the group creator can delete the group'}), 403

            # Delete expense splits
            cursor.execute('''
                DELETE es FROM expense_splits es
                JOIN group_expenses ge ON es.expense_id = ge.id
                WHERE ge.group_id = %s
            ''', (group_id,))
            
            # Delete group expenses
            cursor.execute('DELETE FROM group_expenses WHERE group_id = %s', (group_id,))
            
            # Delete group members
            cursor.execute('DELETE FROM group_members WHERE group_id = %s', (group_id,))
            
            # Delete the group
            cursor.execute('DELETE FROM expense_groups WHERE id = %s', (group_id,))
            
            conn.commit()
            return jsonify({'message': 'Group deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

# Group expense routes
@groups_bp.route('/<int:group_id>/expenses', methods=['POST'])
def create_group_expense(group_id):
    token = request.headers.get('Authorization')
    if not token or not verify_token(token):
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    user_id = verify_token(token)['user_id']
    amount = data.get('amount')
    description = data.get('description')
    paid_by = data.get('paid_by', user_id)
    date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
    notes = data.get('notes', '')
    splits = data.get('splits', [])

    if not all([amount, description]):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Verify user is group member or creator
            cursor.execute(
                '''SELECT g.created_by FROM expense_groups g
                   LEFT JOIN group_members gm ON g.id = gm.group_id
                   WHERE g.id = %s AND (gm.user_id = %s OR g.created_by = %s)''',
                (group_id, user_id, user_id)
            )
            group_info = cursor.fetchone()
            if not group_info:
                return jsonify({'error': 'Not a group member'}), 403

            creator_id = group_info['created_by']

            # Check if paid_by is a virtual member
            cursor.execute('''
                SELECT vm.id, vm.name, gm.group_id
                FROM virtual_members vm
                JOIN group_members gm ON vm.id = gm.virtual_member_id
                WHERE vm.id = %s AND gm.group_id = %s
            ''', (paid_by, group_id))
            paid_by_virtual = cursor.fetchone()

            # Create group expense - if paid_by is not a real user, set it to the group creator
            actual_paid_by = paid_by
            if paid_by_virtual:
                # If a virtual member is paying, we'll record it as the group creator for DB integrity
                actual_paid_by = creator_id
                
                # Store the virtual member name in notes for reference
                notes += f"\nPaid by virtual member: {paid_by_virtual['name']}"

            cursor.execute(
                '''INSERT INTO group_expenses (group_id, paid_by, amount, description, date, notes)
                   VALUES (%s, %s, %s, %s, %s, %s)''',
                (group_id, actual_paid_by, amount, description, date, notes)
            )
            expense_id = cursor.lastrowid

            # Get all real members (users) in the group
            cursor.execute('SELECT user_id FROM group_members WHERE group_id = %s AND user_id IS NOT NULL', (group_id,))
            real_members = cursor.fetchall()
            real_member_ids = [member['user_id'] for member in real_members]

            # If no splits provided, split equally among all real users
            if not splits:
                if not real_members:
                    return jsonify({'error': 'No real members to split expense with'}), 400
                
                # Calculate equal split amount
                split_amount = float(amount) / len(real_members)
                
                # Create splits only for real users
                for member_id in real_member_ids:
                    cursor.execute(
                        '''INSERT INTO expense_splits (expense_id, user_id, amount, is_paid)
                           VALUES (%s, %s, %s, %s)''',
                        (expense_id, member_id, split_amount, member_id == actual_paid_by)
                    )
            else:
                # Create splits for real users only
                for split in splits:
                    user_id_to_check = split['user_id']
                    
                    # Check if this is a virtual member
                    cursor.execute('SELECT 1 FROM virtual_members WHERE id = %s', (user_id_to_check,))
                    is_virtual = cursor.fetchone()
                    
                    if is_virtual:
                        # For virtual members, we'll allocate their share to the creator
                        cursor.execute(
                            '''INSERT INTO expense_splits (expense_id, user_id, amount, is_paid)
                               VALUES (%s, %s, %s, %s)''',
                            (expense_id, creator_id, split['amount'], creator_id == actual_paid_by)
                        )
                    elif user_id_to_check in real_member_ids:
                        # For real users
                        cursor.execute(
                            '''INSERT INTO expense_splits (expense_id, user_id, amount, is_paid)
                               VALUES (%s, %s, %s, %s)''',
                            (expense_id, user_id_to_check, split['amount'], user_id_to_check == actual_paid_by)
                        )

            conn.commit()
            return jsonify({'message': 'Group expense created successfully', 'expense_id': expense_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@groups_bp.route('/<int:group_id>/expenses', methods=['GET'])
def get_group_expenses(group_id):
    token = request.headers.get('Authorization')
    if not token or not verify_token(token):
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = verify_token(token)['user_id']
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Verify user is group member or creator using the improved query
            cursor.execute(
                '''SELECT 1 FROM expense_groups g 
                   WHERE g.id = %s AND (
                       g.created_by = %s OR 
                       EXISTS (SELECT 1 FROM group_members gm WHERE gm.group_id = g.id AND gm.user_id = %s)
                   )''',
                (group_id, user_id, user_id)
            )
            if not cursor.fetchone():
                return jsonify({'error': 'Not authorized to view this group'}), 403

            # Get group expenses with paid by user information
            cursor.execute('''
                SELECT ge.*, u.username as paid_by_name
                FROM group_expenses ge
                LEFT JOIN users u ON ge.paid_by = u.id
                WHERE ge.group_id = %s
                ORDER BY ge.date DESC
            ''', (group_id,))
            expenses = cursor.fetchall()
            
            # For each expense, get the split details and check for virtual payers
            formatted_expenses = []
            for expense in expenses:
                expense_dict = dict(expense)
                
                # Check if this expense was actually paid by a virtual member (noted in notes)
                notes = expense.get('notes', '')
                if notes and 'Paid by virtual member:' in notes:
                    # Extract virtual member name from notes
                    try:
                        virtual_member_name = notes.split('Paid by virtual member:')[1].strip()
                        # Replace the actual payer name with the virtual member name
                        expense_dict['paid_by_name'] = virtual_member_name
                        # Clean up the notes to remove the system annotation
                        expense_dict['notes'] = notes.split('\nPaid by virtual member:')[0]
                    except Exception as e:
                        print(f"Error parsing virtual member from notes: {e}")
                
                cursor.execute('''
                    SELECT es.*, u.username, u.email
                    FROM expense_splits es
                    LEFT JOIN users u ON es.user_id = u.id
                    WHERE es.expense_id = %s
                ''', (expense_dict['id'],))
                splits = cursor.fetchall()
                expense_dict['splits'] = splits
                formatted_expenses.append(expense_dict)
            
            return jsonify(formatted_expenses)
    except Exception as e:
        print(f"Error in get_group_expenses: {str(e)}")  # Add debugging
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@groups_bp.route('/<int:group_id>/expenses/<int:expense_id>', methods=['DELETE'])
def delete_group_expense(group_id, expense_id):
    token = request.headers.get('Authorization')
    if not token or not verify_token(token):
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = verify_token(token)['user_id']
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Verify user is expense creator or group creator
            cursor.execute('''
                SELECT ge.id, ge.paid_by, g.created_by 
                FROM group_expenses ge
                JOIN expense_groups g ON ge.group_id = g.id
                WHERE ge.id = %s AND ge.group_id = %s
            ''', (expense_id, group_id))
            expense = cursor.fetchone()
            
            if not expense:
                return jsonify({'error': 'Expense not found'}), 404
                
            if expense['paid_by'] != user_id and expense['created_by'] != user_id:
                return jsonify({'error': 'Only the expense creator or group creator can delete the expense'}), 403

            # Delete expense splits
            cursor.execute('DELETE FROM expense_splits WHERE expense_id = %s', (expense_id,))
            
            # Delete expense
            cursor.execute('DELETE FROM group_expenses WHERE id = %s', (expense_id,))
            
            conn.commit()
            return jsonify({'message': 'Expense deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@groups_bp.route('/<int:group_id>/balances', methods=['GET'])
def get_group_balances(group_id):
    token = request.headers.get('Authorization')
    if not token or not verify_token(token):
        return jsonify({'error': 'Unauthorized'}), 401

    user_id = verify_token(token)['user_id']
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Verify user is group member or creator with improved query
            cursor.execute(
                '''SELECT 1 FROM expense_groups g 
                   WHERE g.id = %s AND (
                       g.created_by = %s OR 
                       EXISTS (SELECT 1 FROM group_members gm WHERE gm.group_id = g.id AND gm.user_id = %s)
                   )''',
                (group_id, user_id, user_id)
            )
            if not cursor.fetchone():
                return jsonify({'error': 'Not authorized to view this group'}), 403

            # Get only the current user
            cursor.execute('''
                SELECT u.id, u.username, u.email
                FROM users u
                WHERE u.id = %s
            ''', (user_id,))
            current_user = cursor.fetchone()
            
            # Add current user to members list
            members = [current_user] if current_user else []

            # Calculate what each person paid
            cursor.execute('''
                SELECT paid_by, SUM(amount) as paid_amount
                FROM group_expenses
                WHERE group_id = %s
                GROUP BY paid_by
            ''', (group_id,))
            payments = cursor.fetchall()
            
            # Create a map of user_id to paid amount
            paid_map = {payment['paid_by']: float(payment['paid_amount']) for payment in payments}
            
            # Calculate what each person owes
            cursor.execute('''
                SELECT es.user_id, SUM(es.amount) as owed_amount
                FROM expense_splits es
                JOIN group_expenses ge ON es.expense_id = ge.id
                WHERE ge.group_id = %s AND es.is_paid = 0
                GROUP BY es.user_id
            ''', (group_id,))
            debts = cursor.fetchall()
            
            # Create a map of user_id to owed amount
            owed_map = {debt['user_id']: float(debt['owed_amount']) for debt in debts}
            
            # Calculate net balance for each member
            net_balances = []
            for member in members:
                paid = paid_map.get(member['id'], 0)
                owed = owed_map.get(member['id'], 0)
                net = paid - owed
                
                net_balances.append({
                    'id': member['id'],
                    'name': member['username'],
                    'email': member['email'],
                    'amount': net
                })
            
            # Calculate who owes whom
            # Simplify the debts by minimizing the number of transactions
            creditors = sorted([b for b in net_balances if b['amount'] > 0], key=lambda x: x['amount'], reverse=True)
            debtors = sorted([b for b in net_balances if b['amount'] < 0], key=lambda x: x['amount'])
            
            detailed_balances = []
            
            # Calculate transactions
            for creditor in creditors:
                credit_remaining = creditor['amount']
                
                for debtor in debtors:
                    if credit_remaining <= 0 or abs(debtor['amount']) <= 0:
                        continue
                        
                    # Amount to settle between this creditor and debtor
                    amount = min(credit_remaining, abs(debtor['amount']))
                    
                    if amount > 0:
                        detailed_balances.append({
                            'from_id': debtor['id'],
                            'from_name': debtor['name'],
                            'from_email': debtor['email'],
                            'to_id': creditor['id'],
                            'to_name': creditor['name'],
                            'to_email': creditor['email'],
                            'amount': amount
                        })
                        
                        # Update remaining amounts
                        credit_remaining -= amount
                        debtor['amount'] += amount
            
            result = {
                'net_balances': net_balances,
                'detailed_balances': detailed_balances
            }
            
            return jsonify(result)
    except Exception as e:
        print(f"Error in get_group_balances: {str(e)}")  # Add debugging
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@groups_bp.route('/<int:group_id>/settle', methods=['POST'])
def settle_expense(group_id):
    token = request.headers.get('Authorization')
    if not token or not verify_token(token):
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    user_id = verify_token(token)['user_id']
    payer = data.get('payer')
    payee = data.get('payee')
    amount = data.get('amount')

    if not all([payer, payee, amount]):
        return jsonify({'error': 'Missing required fields'}), 400

    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            # Verify user is group member
            cursor.execute(
                'SELECT 1 FROM group_members WHERE group_id = %s AND user_id = %s',
                (group_id, user_id)
            )
            if not cursor.fetchone():
                return jsonify({'error': 'Not a group member'}), 403

            # Verify both payer and payee are group members
            cursor.execute(
                '''SELECT COUNT(*) as count FROM group_members 
                   WHERE group_id = %s AND (user_id = %s OR user_id = %s)''',
                (group_id, payer, payee)
            )
            member_count = cursor.fetchone()['count']
            if member_count != 2:
                return jsonify({'error': 'Both payer and payee must be members of the group'}), 400

            # Create a settlement expense
            current_date = datetime.now().strftime('%Y-%m-%d')
            cursor.execute(
                '''INSERT INTO group_expenses (group_id, paid_by, amount, description, date, notes, is_settlement)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                (group_id, payee, amount, 'Settlement', current_date, f'Settlement from user {payer} to user {payee}', 1)
            )
            expense_id = cursor.lastrowid

            # Create split for the payer (they owe the full amount)
            cursor.execute(
                '''INSERT INTO expense_splits (expense_id, user_id, amount, is_paid)
                   VALUES (%s, %s, %s, %s)''',
                (expense_id, payer, amount, 1)  # Mark as paid since this is a settlement
            )

            conn.commit()
            return jsonify({'message': 'Settlement recorded successfully', 'expense_id': expense_id}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close() 