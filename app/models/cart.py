from flask import current_app as app


class CartItem:
    def __init__(self, uid, pid, p_name, image, firstname, lastname, seller_id, quantity, max_quantity, cart_unit_price, inv_unit_price, date_added, saved_for_later):
        self.uid = uid 
        self.pid = pid 
        self.p_name = p_name
        self.image = image
        self.firstname = firstname
        self.lastname = lastname
        self.seller_id = seller_id
        self.quantity = quantity 
        self.max_quantity = max_quantity
        self.cart_unit_price = cart_unit_price 
        self.inv_unit_price = inv_unit_price
        self.date_added = date_added
        self.saved_for_later = saved_for_later

    @staticmethod
    def get_item(uid, pid, sid, saved_for_later = False):
        rows = app.db.execute('''
SELECT uid, c.pid, name, image, firstname, lastname, c.seller_id, c.quantity, i.quantity, c.unit_price, i.unit_price, date_added, saved_for_later
FROM ((CartItem c JOIN Products p ON p.pid = c.pid) JOIN Users u ON u.id = seller_id) JOIN Inventory i ON (i.pid = c.pid and i.seller_id = c.seller_id)
WHERE uid = :uid AND c.pid = :pid AND c.seller_id = :sid AND saved_for_later = :saved_for_later
''',
                              uid=uid,
                              pid=pid,
                              sid=sid,
                              saved_for_later=saved_for_later)
        if len(rows) == 0:
            return None
        return CartItem(*rows[0])

    @staticmethod
    def get_items_by_user(uid, saved_for_later = False, offset=0, num_items='ALL'):
        
        query = '''SELECT uid, c.pid, name, image, firstname, lastname, c.seller_id, c.quantity, i.quantity, c.unit_price, i.unit_price, date_added, saved_for_later
FROM ((CartItem c JOIN Products p ON p.pid = c.pid) JOIN Users u ON u.id = seller_id) JOIN Inventory i ON (i.pid = c.pid and i.seller_id = c.seller_id)
WHERE uid = :uid AND saved_for_later = :saved_for_later
ORDER BY date_added ASC
OFFSET :offset'''

        if num_items == 'ALL':
            rows = app.db.execute(query + ';',
                                uid=uid,
                                saved_for_later=saved_for_later,
                                offset=offset)

        else:
            rows = app.db.execute(query + '''
LIMIT :num_items;
''',
                                uid=uid,
                                saved_for_later=saved_for_later,
                                offset=offset,
                                num_items=num_items)
        cart_items = [CartItem(*row) for row in rows]

        # check if price has changed, and if so update the price
        for cart_item in cart_items:
            if cart_item.cart_unit_price != cart_item.inv_unit_price:
                CartItem.update_price(uid, cart_item.pid, cart_item.seller_id, cart_item.inv_unit_price)

        return cart_items

    @staticmethod
    def get_total_items_by_user(uid, saved_for_later = False):
        rows = app.db.execute('''
SELECT COUNT(*)
FROM CartItem
WHERE uid = :uid AND saved_for_later = :saved_for_later
''',
                              uid=uid,
                              saved_for_later=saved_for_later)
        return rows[0][0]


    @staticmethod
    def add_item(uid, pid, sid, quantity, price, date_added, saved_for_later = False):
        try:
            rows = app.db.execute("""
INSERT INTO CartItem(uid, pid, seller_id, quantity, unit_price)
VALUES(:uid, :pid, :sid, :quantity, :price)
""",
                                  uid=uid,
                                  pid=pid,
                                  sid=sid,
                                  quantity=quantity,
                                  price=price)
            return True 
        except Exception as e:
            print(str(e))
            return None

    @staticmethod
    def update_quantity(uid, pid, sid, quantity, saved_for_later = False):
        try:
            rows = app.db.execute("""
UPDATE CartItem
SET quantity = :quantity
WHERE uid = :uid AND pid = :pid AND seller_id = :sid AND saved_for_later = :saved_for_later
""",
                                    uid=uid,
                                    pid=pid,
                                    sid=sid,
                                    quantity=quantity,
                                    saved_for_later=saved_for_later)
            return True
        except Exception as e:
            print(str(e))
            return None
    
    @staticmethod
    def update_price(uid, pid, sid, price, saved_for_later = False):
        try:
            rows = app.db.execute("""
UPDATE CartItem
SET unit_price = :price
WHERE uid = :uid AND pid = :pid AND seller_id = :sid AND saved_for_later = :saved_for_later
""",
                                    uid=uid,
                                    pid=pid,
                                    sid=sid,
                                    price=price,
                                    saved_for_later=saved_for_later)
            return True
        except Exception as e:
            print(str(e))
            return None
    
    @staticmethod
    def update_saved_for_later(uid, pid, sid, saved_for_later = False, new_saved_for_later = True):
        try:
            rows = app.db.execute("""
UPDATE CartItem
SET saved_for_later = :new_saved_for_later
WHERE uid = :uid AND pid = :pid AND seller_id = :sid AND saved_for_later = :saved_for_later
""",
                                    uid=uid,
                                    pid=pid,
                                    sid=sid,
                                    saved_for_later=saved_for_later,
                                    new_saved_for_later=new_saved_for_later)
            return True
        except Exception as e:
            print(str(e))
            return None

    @staticmethod
    def delete_item(uid, pid, sid, saved_for_later = False):
        try:
            rows = app.db.execute("""
DELETE FROM CartItem
WHERE uid = :uid AND pid = :pid AND seller_id = :sid AND saved_for_later = :saved_for_later
""",
                                    uid=uid,
                                    pid=pid,
                                    sid=sid,
                                    saved_for_later=saved_for_later)
            return True 
        except Exception as e:
            print(str(e))
            return None

    @staticmethod
    def delete_seller_item(pid, seller_id, saved_for_later = False):
        try:
            rows = app.db.execute("""
DELETE FROM CartItem
WHERE pid = :pid AND seller_id = :seller_id AND saved_for_later = :saved_for_later
""",
                                    pid=pid,
                                    seller_id=seller_id,
                                    saved_for_later=saved_for_later)
            return True 
        except Exception as e:
            print(str(e))
            return None

    @staticmethod
    def delete_all(uid, saved_for_later = False):
        try:
            rows = app.db.execute("""
DELETE FROM CartItem
WHERE uid = :uid AND saved_for_later = :saved_for_later
""",
                                    uid=uid, 
                                    saved_for_later=saved_for_later)
            return True
        except Exception as e:
            print(str(e))
            return None

    @staticmethod 
    def total_cost(uid, saved_for_later = False):
        rows = app.db.execute('''
SELECT SUM(i.unit_price * c.quantity)
FROM CartItem c JOIN Products p ON p.pid = c.pid JOIN Inventory i ON (i.pid = c.pid and i.seller_id = c.seller_id)
WHERE uid = :uid AND saved_for_later = :saved_for_later
''',
                              uid=uid,
                              saved_for_later=saved_for_later)
        subtotal = rows[0][0] if rows[0][0] != None else 0.0
        return subtotal
