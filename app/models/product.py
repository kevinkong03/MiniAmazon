from flask import current_app as app

class Product:
    def __init__(self, pid, cid, category, creator_id, name, description, image, available, rating, unit_price):
        self.pid = pid
        self.cid = cid
        self.category = category
        self.creator_id = creator_id
        self.name = name
        self.description = description
        self.image = image
        self.available = available
        self.rating = rating
        self.unit_price = unit_price

    @staticmethod
    def get(pid):
        rows = app.db.execute('''
SELECT p.pid, p.cid, c.name, p.creator_id, p.name, p.description, p.image, p.available, AVG(pr.rating), i.unit_price
FROM Products p LEFT JOIN ProductReviews pr ON p.pid = pr.pid LEFT JOIN Inventory i ON p.pid = i.pid LEFT JOIN Categories c ON p.cid = c.cid
WHERE p.pid = :pid
GROUP BY p.pid, p.cid, c.name, p.creator_id, p.name, p.description, p.image, p.available, i.unit_price
''',
                              pid=pid)
        return Product(*(rows[0])) if rows else None

    @staticmethod
    def get_all(available=True):
        rows = app.db.execute('''
SELECT p.pid, p.cid, c.name, p.creator_id, p.name, p.description, p.image, p.available, pr.rating, i.unit_price
FROM Products p LEFT JOIN ProductReviews pr ON p.pid = pr.pid LEFT JOIN Inventory i ON p.pid = i.pid LEFT JOIN Categories c ON p.cid = c.cid
WHERE p.available = :available
''',
                              available=available)
        return [Product(*row) for row in rows]
    
    @staticmethod
    def get_by_name(name):
        rows = app.db.execute('''
SELECT p.pid
FROM Products p
WHERE p.name = :name
''',
                              name=name)
        return rows[0][0] if rows else None

    @staticmethod
    def get_total_products(cat='All', avail='False', minPrice=0, maxPrice=9999999, keyword='',firstName='',lastName='', minRating=0):    
        rows = app.db.execute(f'''
SELECT COUNT(*) FROM (
   SELECT DISTINCT ON (i.pid) i.pid as pid, c.name as category, i.seller_id as seller_id, p.name as name, p.available as available, i.unit_price as unit_price 
    FROM (Products p LEFT JOIN Inventory i ON p.pid = i.pid) LEFT JOIN Categories c ON p.cid = c.cid LEFT JOIN ProductReviews pr ON i.pid = pr.pid
    WHERE
        (CASE 
            WHEN :avail = True THEN p.available = true AND LOWER(p.name) LIKE '%' || :keyword || '%' AND COALESCE(pr.rating, 0) >= :minRating
            ELSE LOWER(p.name) LIKE '%' || :keyword || '%' AND COALESCE(pr.rating, 0) >= :minRating
        END)
        AND EXISTS (
            SELECT 1
            FROM Users u JOIN Inventory iv ON u.id = iv.seller_id
            WHERE iv.pid = p.pid AND LOWER(u.firstname) LIKE '%' || :firstName || '%' AND LOWER(u.lastname) LIKE '%' || :lastName || '%'
        )                                       
    GROUP BY i.pid, p.name, c.name, p.image, i.seller_id, i.unit_price, c.name, p.description, i.unit_price, p.available                                                      
) AS distinct_products
WHERE 
    (CASE 
        WHEN :cat = 'All' THEN distinct_products.unit_price >= :minPrice AND distinct_products.unit_price <= :maxPrice
        WHEN (SELECT parent_id FROM Categories WHERE name = :cat) IS NULL THEN distinct_products.unit_price >= :minPrice AND distinct_products.unit_price <= :maxPrice AND distinct_products.category IN (SELECT name FROM Categories WHERE parent_id = (SELECT cid FROM Categories WHERE name = :cat))
        ELSE distinct_products.unit_price >= :minPrice AND distinct_products.unit_price <= :maxPrice AND distinct_products.category = :cat
    END)
''',
                              cat=cat,
                              minPrice=minPrice,
                              maxPrice=maxPrice,
                              avail=avail,
                              keyword=keyword,
                              firstName=firstName,
                              lastName=lastName,
                              minRating=minRating)
        return rows[0][0]
    

    @staticmethod
    def get_all_product_list(sort='price', cat='All', offset=0, num_items=None, avail='False', minPrice=0, maxPrice=9999999,keyword='',firstName='',lastName='', seller=None,minRating=0):
        rows = app.db.execute(f'''
SELECT * FROM (
   SELECT DISTINCT ON (i.pid) i.pid as pid, c.cid as cid, c.name as category, i.seller_id as seller_id, p.name as name, p.description as description, p.image as image, p.available as available, AVG(pr.rating) as avg_rating, i.unit_price as unit_price 
    FROM (Products p LEFT JOIN Inventory i ON p.pid = i.pid) LEFT JOIN Categories c ON p.cid = c.cid LEFT JOIN ProductReviews pr ON i.pid = pr.pid LEFT JOIN Users u ON i.seller_id = u.id
    WHERE
        (CASE 
            WHEN :avail = True THEN p.available = true AND LOWER(p.name) LIKE '%' || :keyword || '%' AND COALESCE(pr.rating, 0) >= :minRating
            ELSE LOWER(p.name) LIKE '%' || :keyword || '%' AND COALESCE(pr.rating, 0) >= :minRating
        END)
        AND EXISTS (
            SELECT 1
            FROM Users u JOIN Inventory iv ON u.id = iv.seller_id
            WHERE iv.pid = p.pid AND LOWER(u.firstname) LIKE '%' || :firstName || '%' AND LOWER(u.lastname) LIKE '%' || :lastName || '%'
        )                     
    GROUP BY i.pid, p.name, c.cid, c.name, p.image, i.seller_id, i.unit_price, c.name, p.description, i.unit_price, p.available                                                      
) AS distinct_products
WHERE 
    (CASE 
        WHEN :cat = 'All' THEN distinct_products.unit_price >= :minPrice AND distinct_products.unit_price <= :maxPrice
        WHEN (SELECT parent_id FROM Categories WHERE name = :cat) IS NULL THEN distinct_products.unit_price >= :minPrice AND distinct_products.unit_price <= :maxPrice AND distinct_products.category IN (SELECT name FROM Categories WHERE parent_id = (SELECT cid FROM Categories WHERE name = :cat))
        ELSE distinct_products.unit_price >= :minPrice AND distinct_products.unit_price <= :maxPrice AND distinct_products.category = :cat
    END) AND 
    (CASE
        WHEN :seller IS NOT NULL THEN pid NOT IN (SELECT pid FROM Inventory WHERE pid = distinct_products.pid AND seller_id = :seller)
        ELSE :seller IS NULL
    END)
ORDER BY 
    (CASE 
        WHEN :sort = 'price' THEN distinct_products.unit_price
        ELSE NULL
    END),
    (CASE 
        WHEN :sort = 'category' THEN distinct_products.category
        ELSE NULL
    END),
    (CASE 
        WHEN :sort != 'category' and :sort != 'price' THEN distinct_products.name
        ELSE NULL
    END)
OFFSET :offset
LIMIT :num_items
''',
                              offset=offset,
                              cat=cat,
                              minPrice=minPrice,
                              maxPrice=maxPrice,
                              avail=avail,
                              keyword=keyword,
                              sort=sort,
                              num_items=num_items,
                              firstName=firstName,
                              lastName=lastName,
                              minRating=minRating,
                              seller=seller)
        return [Product(*row) for row in rows]
    
    
    @staticmethod
    def get_creator_id(pid):
        rows = app.db.execute('''
SELECT creator_id
FROM Products
WHERE pid = :pid
''',
                              pid=pid)
        return rows[0][0]

    @staticmethod
    def update_item(pid, creator_id, description, cid, image):
        try:
            rows = app.db.execute(f"""
    UPDATE Products
    SET description = :description, cid = :cid, image = :image
    WHERE pid = :pid AND creator_id = :creator_id;
    """,
                                    pid=pid,
                                    creator_id=creator_id,
                                    description=description,
                                    cid=cid,
                                    image=image)
            return True 
        except Exception as e:
            print(str(e))
            return None

    @staticmethod
    def update_availability(pid, available):
        try:
            rows = app.db.execute(f"""
    UPDATE Products
    SET available = :available
    WHERE pid = :pid;
    """,
                                    pid=pid,
                                    available=available)
            return True
        except Exception as e:
            print(str(e))
            return None

    @staticmethod
    def get_largest_pid():
        rows = app.db.execute('''
SELECT MAX(pid)
FROM Products
''')
        return rows[0][0] if rows else None

    @staticmethod
    def add_item(cid, creator_id, name, description, image):
        try:
            rows = app.db.execute("""
    INSERT INTO Products (cid, creator_id, name, description, image)
    VALUES(:cid, :seller_id, :name, :description, :image)
    """,
                                    cid=cid,
                                    seller_id=creator_id,
                                    name=name,
                                    description=description,
                                    image=image)
            return True
        except Exception as e:
            print(str(e))
            return None

    @staticmethod
    def get_past_orderItems(uid, offset, num_items):
        rows = app.db.execute('''
    SELECT p.pid, p.cid, c.name, p.creator_id, p.name, p.description, p.image, p.available, pr.rating, i.unit_price
    FROM (SELECT DISTINCT pid FROM OrderItem WHERE order_id IN (SELECT order_id FROM Orders WHERE buyer_id = :uid)) o
    JOIN Products p ON o.pid = p.pid
    LEFT JOIN (SELECT pid, MAX(rating) as rating FROM ProductReviews GROUP BY pid) pr ON p.pid = pr.pid
    LEFT JOIN (SELECT pid, MAX(unit_price) as unit_price FROM Inventory GROUP BY pid) i ON p.pid = i.pid
    LEFT JOIN Categories c ON p.cid = c.cid
    OFFSET :offset
    LIMIT :num_items
    ''',
    uid=uid,
    offset=offset,
    num_items=num_items)
        return [Product(*row) for row in rows]

    @staticmethod
    def get_total_past_orderItems(uid):
        rows = app.db.execute('''
SELECT COUNT(DISTINCT p.pid)
FROM (SELECT DISTINCT pid FROM OrderItem WHERE order_id IN (SELECT order_id FROM Orders WHERE buyer_id = :uid)) o
    JOIN Products p ON o.pid = p.pid
    LEFT JOIN (SELECT pid, MAX(rating) as rating FROM ProductReviews GROUP BY pid) pr ON p.pid = pr.pid
    LEFT JOIN (SELECT pid, MAX(unit_price) as unit_price FROM Inventory GROUP BY pid) i ON p.pid = i.pid
    LEFT JOIN Categories c ON p.cid = c.cid
''',
                              uid=uid)
        return rows[0][0]