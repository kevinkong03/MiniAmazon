from flask import current_app as app


class Inventory:
    def __init__(self, pid, name, image, seller_id, firstname, lastname, unit_price, quantity, category, rating, description):
        self.pid = pid
        self.name = name
        self.image = image
        self.seller_id = seller_id
        self.firstname = firstname
        self.lastname = lastname
        self.unit_price = unit_price
        self.quantity = quantity
        self.category = category
        self.rating = rating
        self.description = description

    @staticmethod
    def get_all(offset, num_items):
        rows = app.db.execute('''
SELECT i.pid, p.name, p.image, i.seller_id, u.firstname, u.lastname, i.unit_price, i.quantity, c.name, pr.rating, description
FROM (Products p JOIN Inventory i ON p.pid = i.pid) JOIN Users u ON i.seller_id = u.id JOIN Categories c ON p.cid = c.cid JOIN ProductReviews pr ON i.pid = pr.pid
OFFSET :offset
LIMIT :num_items                              
''',
                                offset=offset,
                                num_items=num_items)
        return [Inventory(*row) for row in rows]

    @staticmethod
    def get_total_products():
        rows = app.db.execute('''
SELECT COUNT(*)
FROM Inventory
 ''',
                              )
        return rows[0][0]


    @staticmethod
    def get_by_product(pid, offset=0, num_items=None, distinct='False'):
        if distinct == 'False':
            query = '''
            SELECT i.pid, p.name, p.image, i.seller_id, u.firstname, u.lastname, i.unit_price, i.quantity, c.name, AVG(pr.rating), p.description
            FROM (Products p JOIN Inventory i ON p.pid = i.pid) JOIN Users u ON i.seller_id = u.id JOIN Categories c ON p.cid = c.cid LEFT JOIN ProductReviews pr ON i.pid = pr.pid
            WHERE i.pid = :pid
            GROUP BY i.pid, p.name, p.image, i.seller_id, u.firstname, u.lastname, i.unit_price, i.quantity, c.name, p.description
            ORDER BY i.pid, i.unit_price
            OFFSET :offset
            LIMIT :num_items
            '''
        else:
            query = '''
            SELECT DISTINCT ON (i.pid) i.pid, p.name, p.image, i.seller_id, u.firstname, u.lastname, i.unit_price, i.quantity, c.name, AVG(pr.rating), p.description
            FROM (Products p JOIN Inventory i ON p.pid = i.pid) JOIN Users u ON i.seller_id = u.id JOIN Categories c ON p.cid = c.cid LEFT JOIN ProductReviews pr ON i.pid = pr.pid
            WHERE i.pid = :pid
            GROUP BY i.pid, p.name, p.image, i.seller_id, u.firstname, u.lastname, i.unit_price, i.quantity, c.name, p.description
            ORDER BY i.pid, i.unit_price
            OFFSET :offset
            LIMIT :num_items
            '''

        rows = app.db.execute(query, pid=pid, offset=offset, num_items=num_items)
        return [Inventory(*row) for row in rows]

    @staticmethod
    def get_by_seller(seller_id, offset, num_items, keyword=''):
        rows = app.db.execute('''
SELECT i.pid, p.name, p.image, i.seller_id, u.firstname, u.lastname, i.unit_price, i.quantity, c.name,  AVG(pr.rating), description
FROM (Products p JOIN Inventory i ON p.pid = i.pid) JOIN Users u ON i.seller_id = u.id JOIN Categories c ON p.cid = c.cid LEFT JOIN ProductReviews pr ON i.pid = pr.pid
WHERE i.seller_id = :seller_id AND LOWER(p.name) LIKE '%' || :keyword || '%'
GROUP BY i.pid, p.name, p.image, i.seller_id, u.firstname, u.lastname, i.unit_price, i.quantity, c.name, description
ORDER BY p.name
OFFSET :offset
LIMIT :num_items
''',
                              seller_id=seller_id,
                              offset=offset,
                              num_items=num_items,
                              keyword=keyword)
        return [Inventory(*row) for row in rows]

    @staticmethod
    def get_total_items(seller_id, keyword=''):
        rows = app.db.execute('''
SELECT COUNT(*)
FROM Products p JOIN Inventory i ON p.pid = i.pid
WHERE seller_id = :seller_id AND LOWER(p.name) LIKE '%' || :keyword || '%'
 ''',
                              seller_id=seller_id,
                              keyword=keyword)
        return rows[0][0]
    
    @staticmethod
    def get_total_sellers(pid):
        rows = app.db.execute('''
SELECT COUNT(DISTINCT seller_id)
FROM Inventory
WHERE pid = :pid
 ''',
                              pid=pid)
        return rows[0][0]
        
    @staticmethod
    def get_by_product_and_seller(pid, seller_id):
        rows = app.db.execute('''
SELECT i.pid, p.name, p.image, i.seller_id, u.firstname, u.lastname, i.unit_price, i.quantity, c.name, pr.rating, description
FROM (Products p JOIN Inventory i ON p.pid = i.pid) JOIN Users u ON i.seller_id = u.id JOIN Categories c ON p.cid = c.cid LEFT JOIN ProductReviews pr ON i.pid = pr.pid
WHERE i.pid = :pid and i.seller_id = :seller_id
''',
                              pid=pid,
                              seller_id=seller_id)
        return Inventory(*(rows[0])) if rows else None


    @staticmethod
    def get_all_sorted_price(offset, num_items):
        rows = app.db.execute('''
SELECT i.pid, p.name, p.image, i.seller_id, u.firstname, u.lastname, i.unit_price, i.quantity, c.name, pr.rating, description
FROM (Products p JOIN Inventory i ON p.pid = i.pid) JOIN Users u ON i.seller_id = u.id JOIN Categories c ON p.cid = c.cid LEFT JOIN ProductReviews pr ON i.pid = pr.pid
ORDER BY i.unit_price DESC
OFFSET :offset
LIMIT :num_items
''',
                              offset=offset,
                              num_items=num_items)
        return [Inventory(*row) for row in rows]
    
    @staticmethod
    def get_by_category(cid):
        rows = app.db.execute('''
SELECT i.pid, p.name, p.image, i.seller_id, u.firstname, u.lastname, i.unit_price, i.quantity, c.name, pr.rating, description
FROM (Products p JOIN Inventory i ON p.pid = i.pid) JOIN Users u ON i.seller_id = u.id JOIN Categories c ON p.cid = c.cid LEFT JOIN ProductReviews pr ON i.pid = pr.pid
WHERE p.cid = :cid
''',
                              cid=cid)
        return Inventory(*(rows[0])) if rows else None

    @staticmethod
    def update_item(pid, sid, unit_price, quantity):
        try:
            rows = app.db.execute(f"""
    UPDATE Inventory
    SET unit_price = :unit_price, quantity = :quantity
    WHERE pid = :pid AND seller_id = :sid;
    """,
                                    pid=pid,
                                    sid=sid,
                                    unit_price=unit_price,
                                    quantity=quantity)
            return True 
        except Exception as e:
            print(str(e))
            return None
            
    @staticmethod
    def add_item(pid, seller_id, unit_price, quantity):
        try:
            rows = app.db.execute("""
INSERT INTO Inventory(pid, seller_id, unit_price, quantity)
VALUES(:pid, :seller_id, :unit_price, :quantity)
""",
                                  pid=pid,
                                  seller_id=seller_id,
                                  unit_price=unit_price,
                                  quantity=quantity)
            return True 
        except Exception as e:
            # likely email already in use; better error checking and reporting needed;
            # the following simply prints the error to the console:
            print(str(e))
            return None
        
    @staticmethod
    def delete(pid, seller_id):
        try:
            rows = app.db.execute("""
DELETE FROM Inventory
WHERE pid = :pid AND seller_id = :seller_id
""",
                                    pid=pid,
                                    seller_id=seller_id)
            return True 
        except Exception as e:
            print(str(e))
            return None
        
    @staticmethod
    def get_all_sellers():
        sellers = app.db.execute('''
SELECT DISTINCT seller_id as sid, u.firstname, u.lastname
FROM Inventory i JOIN Users u ON i.seller_id = u.id
''')
        return sellers

    @staticmethod
    def get_monthly_sales_from_last_12_months(seller_id):
        rows = app.db.execute('''
            SELECT months, COALESCE(sales, 0) as total_sales
            FROM generate_series(1, 12) AS months
            LEFT JOIN (
                SELECT DATE_TRUNC('month', order_date) as month, SUM(quantity*unit_price) as sales
                FROM OrderItem o JOIN Orders r ON o.order_id = r.order_id
                WHERE seller_id = :seller_id AND fulfillment_status = TRUE AND order_date > NOW() - INTERVAL '1 year'
                GROUP BY month
            ) AS sales_data ON EXTRACT(MONTH FROM sales_data.month)::INTEGER = months
            GROUP BY months, sales
            ORDER BY months
        ''',
        seller_id=seller_id)
        return rows

    @staticmethod
    def get_yearly_sales_from_last_5_years(seller_id):
        rows = app.db.execute('''
            SELECT years, COALESCE(sales, 0) as total_sales
            FROM generate_series(2018, 2023) AS years
            LEFT JOIN (
                SELECT DATE_TRUNC('year', order_date) as year, SUM(quantity*unit_price) as sales
                FROM OrderItem o JOIN Orders r ON o.order_id = r.order_id
                WHERE seller_id = :seller_id AND fulfillment_status = TRUE AND order_date > NOW() - INTERVAL '5 years'
                GROUP BY year
            ) AS sales_data ON EXTRACT(YEAR FROM sales_data.year)::INTEGER = years
            GROUP BY years, sales
            ORDER BY years
        ''',
        seller_id=seller_id)
        return rows

    @staticmethod
    def get_unique_items_sold_from_last_12_months(seller_id):
        rows = app.db.execute('''
            SELECT months, COALESCE(items, 0) as unique_items
            FROM generate_series(1, 12) AS months
            LEFT JOIN (
                SELECT DATE_TRUNC('month', order_date) as month, COUNT(DISTINCT o.pid) as items
                FROM OrderItem o JOIN Orders r ON o.order_id = r.order_id
                WHERE seller_id = :seller_id AND fulfillment_status = TRUE AND order_date > NOW() - INTERVAL '1 year'
                GROUP BY month
            ) AS items_data ON EXTRACT(MONTH FROM items_data.month)::INTEGER = months
            GROUP BY months, items
            ORDER BY months
        ''',
        seller_id=seller_id)
        return rows

    @staticmethod
    def does_product_exist_in_inventory(pid, seller_id):
        rows = app.db.execute('''
SELECT EXISTS (
    SELECT 1
    FROM Inventory
    WHERE pid = :pid AND seller_id = :seller_id
)
''',
                              pid=pid,
                              seller_id=seller_id)
        return rows[0][0]
