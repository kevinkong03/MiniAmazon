from flask import current_app as app
from datetime import datetime

class Order:
    def __init__(self, order_id, buyer_id, order_status, order_date, total_quantity, subtotal, address, firstname, lastname):
        self.order_id = order_id 
        self.buyer_id = buyer_id 
        self.order_status = order_status 
        self.order_date = order_date.strftime("%B %d, %Y")
        self.total_quantity = total_quantity 
        self.subtotal = subtotal
        self.address = address
        self.firstname = firstname
        self.lastname = lastname


    @staticmethod
    def get_orders_by_buyer(uid, offset, num_items):
        rows = app.db.execute('''
SELECT o.order_id, buyer_id, order_status, order_date, SUM(quantity), SUM(quantity*unit_price), address, firstname, lastname
FROM (Orders r JOIN OrderItem o ON r.order_id = o.order_id) JOIN Users u ON buyer_id = u.id
WHERE r.buyer_id = :uid
GROUP BY o.order_id, r.buyer_id, order_status, order_date, address, firstname, lastname
ORDER BY order_date DESC
OFFSET :offset
LIMIT :num_items;
''',
                              uid=uid,
                              offset=offset,
                              num_items=num_items)
        return [Order(*row) for row in rows] if rows else []

    @staticmethod
    def get_fulfilled_orders_by_seller(uid, offset, num_items, keyword):
        rows = app.db.execute('''
    SELECT o.order_id, buyer_id, order_status, order_date, SUM(quantity), SUM(quantity*unit_price), address, firstname, lastname
    FROM ((Orders r JOIN OrderItem o ON r.order_id = o.order_id) JOIN Users u ON buyer_id = u.id) JOIN Products p ON o.pid = p.pid
    WHERE o.seller_id = :uid AND NOT EXISTS (SELECT * FROM OrderItem WHERE order_id = o.order_id AND seller_id = :uid AND fulfillment_status = false)
    GROUP BY o.order_id, r.buyer_id, order_status, order_date, address, firstname, lastname
    HAVING COUNT(DISTINCT CASE WHEN LOWER(p.name) LIKE '%' || :keyword || '%' THEN p.pid END) > 0
    ORDER BY order_date DESC
    OFFSET :offset
    LIMIT :num_items;
    ''',
                              uid=uid,
                              offset=offset,
                              num_items=num_items,
                              keyword=keyword)
        return [Order(*row) for row in rows] if rows else []

    @staticmethod
    def get_unfulfilled_orders_by_seller(uid, offset, num_items, keyword):
        rows = app.db.execute('''
SELECT o.order_id, buyer_id, order_status, order_date, SUM(quantity), SUM(quantity*unit_price), address, firstname, lastname
FROM ((Orders r JOIN OrderItem o ON r.order_id = o.order_id) JOIN Users u ON buyer_id = u.id) JOIN Products p ON o.pid = p.pid
WHERE o.seller_id = :uid AND EXISTS (SELECT * FROM OrderItem WHERE order_id = o.order_id AND seller_id = :uid AND fulfillment_status = false)
GROUP BY o.order_id, r.buyer_id, order_status, order_date, address, firstname, lastname
HAVING COUNT(DISTINCT CASE WHEN LOWER(p.name) LIKE '%' || :keyword || '%' THEN p.pid END) > 0
ORDER BY order_date DESC
OFFSET :offset
LIMIT :num_items;
''',
                              uid=uid,
                              offset=offset,
                              num_items=num_items,
                              keyword=keyword)
        return [Order(*row) for row in rows] if rows else []

    @staticmethod
    def get_total_orders_by_buyer(uid):
        rows = app.db.execute('''
SELECT COUNT(*)
FROM Orders
WHERE buyer_id = :uid
''',
                              uid=uid)
        return rows[0][0]

    @staticmethod
    def get_total_orders_by_seller(uid, f_or_unf, keyword=''):
        rows = app.db.execute('''
    SELECT COUNT(DISTINCT o.order_id)
    FROM OrderItem o JOIN Products p ON o.pid = p.pid
    WHERE o.seller_id = :uid AND 
        CASE 
            WHEN :f_or_unf = 'f' THEN NOT EXISTS (SELECT * FROM OrderItem WHERE seller_id = :uid AND order_id = o.order_id AND fulfillment_status = false)
            ELSE EXISTS (SELECT * FROM OrderItem WHERE seller_id = :uid AND order_id = o.order_id AND fulfillment_status = false)
        END
    AND LOWER(p.name) LIKE '%' || :keyword || '%'
    ''',
                              uid=uid,
                              f_or_unf=f_or_unf,
                              keyword=keyword)
        return rows[0][0]

    @staticmethod
    def get_order(order_id):
        rows = app.db.execute('''
SELECT o.order_id, buyer_id, order_status, order_date, SUM(quantity), SUM(quantity*unit_price), address, firstname, lastname
FROM (Orders r JOIN OrderItem o ON r.order_id = o.order_id) JOIN Users u ON buyer_id = u.id
WHERE o.order_id = :order_id
GROUP BY o.order_id, r.buyer_id, order_status, order_date, address, firstname, lastname;
''',
                                order_id=order_id)
        return Order(*(rows[0])) if rows else []   

    @staticmethod 
    def add_order(buyer_id, order_date):
        try:
            rows = app.db.execute('''
    INSERT INTO Orders(buyer_id, order_date)
    VALUES(:buyer_id, :order_date)
    RETURNING order_id;
    ''',
                                buyer_id=buyer_id,
                                order_date=order_date)
            return rows[0][0]
        except Exception as e:
            print(str(e))
            return None

    @staticmethod
    def update_order_status(order_id, order_status):
        try:
            rows = app.db.execute('''
    UPDATE Orders
    SET order_status = :order_status
    WHERE order_id = :order_id
    ''',
                                order_id=order_id,
                                order_status=order_status)
            return True
        except Exception as e:
            print(str(e))
            return None

class OrderItem:
    def __init__(self, order_id, order_date, pid, p_name, image, firstname, lastname, seller_id, quantity, unit_price, fulfillment_status, fulfillment_date):
        self.order_id = order_id
        self.order_date = order_date
        self.pid = pid
        self.p_name = p_name
        self.image = image
        self.firstname = firstname
        self.lastname = lastname
        self.seller_id = seller_id
        self.quantity = quantity
        self.unit_price = unit_price
        self.fulfillment_status = fulfillment_status
        self.fulfillment_date = fulfillment_date

    @staticmethod
    def get_items_by_order(order_id, offset, num_items):
        rows = app.db.execute('''
SELECT o.order_id, order_date, o.pid, name, image, firstname, lastname, seller_id, quantity, unit_price, fulfillment_status, fulfillment_date
FROM ((OrderItem o JOIN Products p ON o.pid = p.pid) JOIN Orders r ON r.order_id = o.order_id) JOIN Users u ON u.id = seller_id
WHERE o.order_id = :order_id
ORDER BY order_date DESC
OFFSET :offset
LIMIT :num_items;
''',
                              order_id=order_id,
                              offset=offset,
                              num_items=num_items)
        return [OrderItem(*row) for row in rows] if rows else []

    @staticmethod
    def get_total_items_by_order(order_id):
        rows = app.db.execute('''
SELECT COUNT(*)
FROM OrderItem
WHERE order_id = :order_id
''',
                              order_id=order_id)
        return rows[0][0]

    
    @staticmethod
    def add_order_details(order_id, pid, seller_id, quantity, unit_price):
        try:
            rows = app.db.execute('''
    INSERT INTO OrderItem(order_id, pid, seller_id, quantity, unit_price)
    VALUES(:order_id, :pid, :seller_id, :quantity, :unit_price)
    ''',
                                order_id=order_id,
                                pid=pid,
                                seller_id=seller_id,
                                quantity=quantity,
                                unit_price=unit_price)
            return True
        except Exception as e:
            print(str(e))
            return None

    @staticmethod
    def get_items_for_order(order_id, seller_id):
        rows = app.db.execute('''
SELECT o.order_id, order_date, o.pid, name, image, firstname, lastname, seller_id, quantity, unit_price, fulfillment_status, fulfillment_date
FROM ((OrderItem o JOIN Products p ON o.pid = p.pid) JOIN Orders r ON r.order_id = o.order_id) JOIN Users u ON u.id = seller_id
WHERE o.order_id = :order_id AND seller_id = :seller_id
ORDER BY order_date DESC;
''',
                              order_id=order_id,
                              seller_id=seller_id)
        return [OrderItem(*row) for row in rows] if rows else []

    @staticmethod
    def update_fulfillment_status(order_id, pid, seller_id, fulfillment_status):
        time_added = datetime.now()
        try:
            rows = app.db.execute('''
    UPDATE OrderItem
    SET fulfillment_status = :fulfillment_status, 
        fulfillment_date = CASE 
            WHEN :fulfillment_status = True THEN :time_added
            ELSE NULL
        END
    WHERE order_id = :order_id AND pid = :pid AND seller_id = :seller_id
    ''',
                                order_id=order_id,
                                pid=pid,
                                seller_id=seller_id,
                                fulfillment_status=fulfillment_status,
                                time_added=time_added)
            return True
        except Exception as e:
            print(str(e))
            return None

    @staticmethod
    def check_fulfillment_status(order_id):
        rows = app.db.execute('''
SELECT NOT EXISTS(SELECT * FROM OrderItem WHERE order_id = :order_id AND fulfillment_status = false)
''',
                              order_id=order_id)
        return rows[0][0]
    
    @staticmethod
    def get_items_by_buyer_and_seller(buyer_id, seller_id):
        rows = app.db.execute('''
SELECT o.order_id, order_date, o.pid, name, image, firstname, lastname, seller_id, quantity, unit_price, fulfillment_status, fulfillment_date
FROM ((OrderItem o JOIN Products p ON o.pid = p.pid) JOIN Orders r ON r.order_id = o.order_id) JOIN Users u ON u.id = seller_id
WHERE buyer_id = :buyer_id AND seller_id = :seller_id
ORDER BY order_date DESC;
''',
                              buyer_id=buyer_id,
                              seller_id=seller_id)
        return [OrderItem(*row) for row in rows] if rows else []
