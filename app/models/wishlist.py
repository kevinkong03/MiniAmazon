from flask import current_app as app
from datetime import datetime



class WishlistItem:
    def __init__(self, uid, pid, time_added, name, image):
        self.uid = uid
        self.pid = pid
        self.time_added = time_added
        self.name = name
        self.image = image

    @staticmethod
    def get_by_user(uid, offset, num_items):
        rows = app.db.execute('''
SELECT w.uid, w.pid, w.time_added, p.name, p.image
FROM Wishlist w JOIN Products p ON w.pid = p.pid
WHERE w.uid = :uid
ORDER BY w.time_added DESC
OFFSET :offset
LIMIT :num_items
''',
                              uid=uid,
                              offset=offset,
                              num_items=num_items)
        return [WishlistItem(*row) for row in rows]
    
    @staticmethod
    def get_total_by_user(uid):
        rows = app.db.execute('''
SELECT COUNT(*)
FROM Wishlist w JOIN Products p ON w.pid = p.pid
WHERE uid = :uid

''',
                              uid=uid)
        return rows[0][0]



    @staticmethod
    def add_wishlist(uid, pid):
        time_added = datetime.now()

        wishlist_data = {
            'uid': uid,
            'pid': pid,
            'time_added': time_added
        }

        try:
            # Insert data into database
            rows = app.db.execute(f"""
                INSERT INTO Wishlist (uid, pid, time_added)
                VALUES (:uid, :pid, :time_added)
                RETURNING uid, pid, time_added
            """,
            uid=uid,
            pid=pid,
            time_added=time_added)

            return True
        except Exception as e:
            # likely email already in use; better error checking and reporting needed;
            # the following simply prints the error to the console:
            print(str(e))
            return None
        
    @staticmethod
    def delete_item(uid, pid):
        try:
            rows = app.db.execute("""
DELETE FROM Wishlist
WHERE uid = :uid AND pid = :pid
""",
                                    uid=uid,
                                    pid=pid,
                                    )
            return True 
        except Exception as e:
            print(str(e))
            return None

    @staticmethod
    def delete_all(uid):
        try:
            rows = app.db.execute("""
DELETE FROM Wishlist
WHERE uid = :uid
""",
                                    uid=uid)
            return True
        except Exception as e:
            print(str(e))
            return None