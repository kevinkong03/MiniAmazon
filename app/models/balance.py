from flask import current_app as app
from datetime import datetime, timedelta
from calendar import month_abbr

import csv

class Balance():
    def __init__(self, uid, timestamp, amount, transaction, related_order_id):
        self.uid = uid
        self.timestamp = timestamp
        self.amount = amount
        self.transaction = transaction
        self.related_order_id = related_order_id

    @staticmethod
    def get_balance_history_by_uid(uid, offset, num_items):
        rows = app.db.execute('''
SELECT timestamp, amount, transaction, related_order_id
FROM Balances
WHERE uid = :uid
ORDER BY timestamp DESC  
OFFSET :offset
LIMIT :num_items                           
''',
                              uid=uid,
                              offset=offset,
                              num_items=num_items)
        return [row for row in rows] if rows else []
    
    @staticmethod
    def get_months_average_by_uid(uid):
        all_months = list(month_abbr)[1:]
        start_date = datetime.now() - timedelta(days=365)

        # Find the first balance amount in the current year
        first_balance_query = app.db.execute('''
SELECT amount
FROM Balances
WHERE uid = :uid AND timestamp >= NOW() - INTERVAL '12 months'
ORDER BY timestamp
LIMIT 1
''', uid=uid)

        first_balance = float(first_balance_query[0][0]) if first_balance_query else 0.0
        

        rows = app.db.execute('''
            SELECT TO_CHAR(timestamp, 'Mon') AS month, AVG(amount) AS average_amount
            FROM Balances
            WHERE uid = :uid AND
                timestamp >= NOW() - INTERVAL '12 months'
            GROUP BY month
            ORDER BY month
        ''', uid=uid)

        average_dict = {row.month: row.average_amount for row in rows}
        for month in all_months:
            month_average = average_dict.get(month, 0)
            if month_average == 0:
                month_average = first_balance
            average_dict[month] = month_average
            
        months = all_months    
        averages = [average_dict.get(month, 0) for month in all_months]

        return months, averages

    def get_total_balances_by_user(uid):
        rows = app.db.execute('''
SELECT COUNT(*)
FROM Balances
WHERE uid = :uid
''',
                              uid=uid)
        return int(rows[0][0]) if rows else 0

    @staticmethod
    def get_current_balance_by_uid(uid):
        rows = app.db.execute('''
SELECT amount
FROM Balances
WHERE uid = :uid                              
ORDER BY timestamp DESC;
''',
                              uid=uid)
        return float(rows[0][0]) if rows else 0
    
    @staticmethod
    def add_balance(uid, timestamp, amount, transaction, related_order_id):
        try:
            # Insert the data into your database
            rows = app.db.execute(f"""
            INSERT INTO Balances (uid, timestamp, amount, transaction, related_order_id)
            VALUES (:uid, :timestamp, :amount, :transaction, :related_order_id)
            RETURNING uid, timestamp, amount, transaction, related_order_id
            """,
            uid=uid,
            timestamp=timestamp,
            amount=amount,
            transaction=transaction,
            related_order_id=related_order_id)

            return True
        except Exception as e:
            # Handle the exception or log it as needed
            print(str(e))
            return None

    @staticmethod
    def get_total_balance_history_entries_by_uid(uid):
        rows = app.db.execute('''
SELECT COUNT(*)
FROM CartItem
WHERE uid = :uid
''',
                              uid=uid)
        return rows[0][0]

