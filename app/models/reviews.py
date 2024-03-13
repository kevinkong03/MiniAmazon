from flask import current_app as app
from datetime import datetime
import csv


class Review:
    def __init__(self, buyer_id, product_id, p_name, title, rating, message, upvote_count, timestamp):
        self.buyer_id = buyer_id
        self.product_id = product_id
        self.p_name = p_name
        self.title = title
        self.rating = rating
        self.message = message
        self.upvote_count = upvote_count
        self.timestamp = timestamp

    @staticmethod
    def get_recent_reviews_by_user(user_id, offset, num_reviews):
        #if review_type not in ['ProductReviews', 'SellerReviews']:
        #    raise ValueError("Invalid review_type.")

        rows = app.db.execute(f'''
SELECT buyer_id, pr.pid, name, title, rating, message, upvote_count, timestamp
FROM ProductReviews pr JOIN Products p ON pr.pid = p.pid
WHERE buyer_id = :user_id
ORDER BY timestamp DESC
OFFSET :offset
LIMIT :num_reviews
''',
                                user_id=user_id,
                                offset=offset,
                                num_reviews=num_reviews)

        return [Review(*row) for row in rows]
    
    @staticmethod
    def get_top_reviews_by_user(user_id, offset, num_reviews):
        #if review_type not in ['ProductReviews', 'SellerReviews']:
        #    raise ValueError("Invalid review_type.")

        rows = app.db.execute(f'''
SELECT buyer_id, pr.pid, name, title, rating, message, upvote_count, timestamp
FROM ProductReviews pr JOIN Products p ON pr.pid = p.pid
WHERE buyer_id = :user_id
ORDER BY upvote_count DESC
OFFSET :offset
LIMIT :num_reviews
''',
                                user_id=user_id,
                                offset=offset,
                                num_reviews=num_reviews)

        return [Review(*row) for row in rows]

    @staticmethod
    def get_total_reviews_by_user(user_id):
        rows = app.db.execute(f'''
SELECT COUNT(*)
FROM ProductReviews
WHERE buyer_id = :user_id
''', 
                                user_id=user_id)

        return rows[0][0]
    
    @staticmethod
    def get_recent_reviews_by_seller(user_id, offset, num_reviews):
        #if review_type not in ['ProductReviews', 'SellerReviews']:
        #    raise ValueError("Invalid review_type.")

        rows = app.db.execute(f'''
SELECT buyer_id, pr.pid, name, title, rating, message, upvote_count, timestamp
FROM ProductReviews pr JOIN Products p ON pr.pid = p.pid JOIN Users U ON pr.buyer_id = U.id
WHERE creator_id = :user_id
ORDER BY timestamp DESC
OFFSET :offset
LIMIT :num_reviews
''',
                                user_id=user_id,
                                offset=offset,
                                num_reviews=num_reviews)

        return [Review(*row) for row in rows]
        
    
    @staticmethod
    def get_top_reviews_by_seller(user_id, offset, num_reviews):
        #if review_type not in ['ProductReviews', 'SellerReviews']:
        #    raise ValueError("Invalid review_type.")

        rows = app.db.execute(f'''
SELECT buyer_id, pr.pid, name, title, rating, message, upvote_count, timestamp
FROM ProductReviews pr JOIN Products p ON pr.pid = p.pid JOIN Users U ON pr.buyer_id = U.id
WHERE creator_id = :user_id
ORDER BY upvote_count DESC
OFFSET :offset
LIMIT :num_reviews
''',
                                user_id=user_id,
                                offset=offset,
                                num_reviews=num_reviews)

        return [Review(*row) for row in rows]

    @staticmethod
    def get_total_reviews_by_seller(user_id):
        rows = app.db.execute(f'''
SELECT COUNT(*)
FROM ProductReviews pr JOIN Products p ON pr.pid = p.pid
WHERE creator_id = :user_id
''', 
                                user_id=user_id)

        return rows[0][0]

    @staticmethod
    def add_review(buyer_id, pid, title, rating, message,review_type):
        if review_type not in ['ProductReviews', 'SellerReviews']:
            raise ValueError("Invalid review_type.")

        timestamp = datetime.now()
        
        # Create a dictionary for the review data
        review_data = {
            'buyer_id': buyer_id,
            'pid': pid,
            'title': title,
            'rating': rating,
            'message': message,
            'upvote_count': 0,  # You may adjust this value as needed
            'timestamp': timestamp
        }

        try:
            # Insert the data into your database
            rows = app.db.execute(f"""
            INSERT INTO {review_type} (buyer_id, pid, title, rating, message, upvote_count, timestamp)
            VALUES (:buyer_id, :pid, :title, :rating, :message, 0, :timestamp)
            RETURNING buyer_id, pid, title, rating, message, upvote_count, timestamp
            """,
            buyer_id=buyer_id,
            pid=pid,
            title=title,
            rating=rating,
            message=message,
            timestamp=timestamp)

            return Review(buyer_id, pid, None, title, rating, message, 0, timestamp)  # Replace 'None' with the actual 'p_name' value
        except Exception as e:
            # Handle the exception or log it as needed
            print(str(e))
            return None
    
    @staticmethod
    def average_rating(uid):
        rows = app.db.execute('''
SELECT AVG(pr.rating)
FROM ProductReviews pr 
WHERE buyer_id = :uid
GROUP BY buyer_id
''',
                              uid=uid)
        return float(rows[0][0]) if rows else None
    
    @staticmethod
    def average_rating_by_seller(uid):
        rows = app.db.execute('''
SELECT AVG(pr.rating)
FROM ProductReviews pr join Products p on pr.pid = p.pid
WHERE creator_id = :uid
GROUP BY creator_id
''',
                              uid=uid)
        return float(rows[0][0]) if rows else None
    
    @staticmethod
    def update_upvote(uid, pname, upvote_count):
        app.db.execute(
            '''
            UPDATE ProductReviews
            SET upvote_count = :upvote_count
            WHERE buyer_id = :uid
                AND pid = (SELECT pid FROM Products WHERE name = :pname)
            ''',
            uid=uid,
            pname=pname,
            upvote_count=upvote_count
        )
        
        return True
    
    @staticmethod
    def update_review(buyer_id, pid, title, rating, message):
        rows=app.db.execute(f'''
UPDATE ProductReviews
SET
    buyer_id = :buyer_id,
    pid = :pid,
    title = :title, 
    rating = :rating, 
    message = :message
WHERE
     buyer_id = :buyer_id AND
     pid = :pid
                ''',
                        buyer_id=buyer_id,
                        pid=pid,
                        title=title,
                        rating=rating,
                        message=message
            )
        return rows

    @staticmethod
    def delete_review(buyer_id, pid):
        rows=app.db.execute(f'''
DELETE FROM ProductReviews
WHERE
                buyer_id = :buyer_id AND
                pid = :pid;
                            ''',
                        buyer_id=buyer_id,
                        pid=pid
            )
        return rows

    @staticmethod
    def get_all_review_for_product(pid, offset=0, num_items=None):
        #if review_type not in ['ProductReviews', 'SellerReviews']:
        #    raise ValueError("Invalid review_type.")

        rows = app.db.execute(f'''
SELECT buyer_id, pr.pid, name, title, rating, message, upvote_count, timestamp
FROM ProductReviews pr JOIN Products p ON pr.pid = p.pid
WHERE p.pid = :pid
ORDER BY timestamp DESC
OFFSET :offset
LIMIT :num_items
''',
                                pid=pid,
                                offset=offset,
                                num_items=num_items
                                )

        return [Review(*row) for row in rows]
    
    @staticmethod
    def have_rated_before(pid,current_uid):
        #if review_type not in ['ProductReviews', 'SellerReviews']:
        #    raise ValueError("Invalid review_type.")

        rows = app.db.execute(f'''
SELECT buyer_id, pr.pid, name, title, rating, message, upvote_count, timestamp
FROM ProductReviews pr JOIN Products p ON pr.pid = p.pid
WHERE p.pid = :pid and buyer_id = :current_uid
''',
                                pid=pid,
                                current_uid=current_uid)

        return [Review(*row) for row in rows]

    @staticmethod
    def get_total_reviews_by_product(pid):
        rows = app.db.execute(f'''
            SELECT COUNT(*)
            FROM ProductReviews
            WHERE pid = :pid
        ''', 
        pid=pid)

        return rows[0][0]

    @staticmethod
    def get_review(pid,uid):
        #if review_type not in ['ProductReviews', 'SellerReviews']:
        #    raise ValueError("Invalid review_type.")

        rows = app.db.execute(f'''
SELECT buyer_id, P.pid, P.name, title, rating, message, upvote_count, timestamp
FROM ProductReviews join Products P on ProductReviews.pid = P.pid
WHERE P.pid = :pid and buyer_id = :uid 
''',
                                pid=pid,
                                uid=uid)

         # Check if a row was returned
        return Review(*rows[0]) if rows else None
    
class SellerReview:
    def __init__(self, buyer_id, seller_id,title, rating, message, upvote_count, timestamp):
        self.buyer_id = buyer_id
        #self.buyer_name = buyer_name
        #self.seller_id = seller_id
        self.seller_id = seller_id
        self.title = title
        self.rating = rating
        self.message = message
        self.upvote_count = upvote_count
        self.timestamp = timestamp

    @staticmethod
    def get_review(seller_id,uid):
        rows = app.db.execute(f'''   
            SELECT *
            FROM SellerReviews SR 
            WHERE buyer_id = :uid
                AND seller_id = :seller_id
        ''',
       seller_id=seller_id,
       uid=uid)

        return SellerReview(*rows[0]) if rows else None

   
    @staticmethod
    def get_recent_reviews_by_user(user_id, offset, num_reviews):
        rows = app.db.execute(f'''   
            SELECT buyer_id,  SR.seller_id, title, rating, message, upvote_count, timestamp
            FROM SellerReviews SR 
            WHERE buyer_id = :user_id
            ORDER BY timestamp DESC
            OFFSET :offset
            LIMIT :num_reviews
        ''',
        user_id=user_id,
        offset=offset,
        num_reviews=num_reviews)

        return [SellerReview(*row) for row in rows]
    
    @staticmethod
    def get_top_reviews_by_user(user_id, offset, num_reviews):
        timestamp = datetime.now()
        rows = app.db.execute(f'''   
            SELECT buyer_id,  SR.seller_id, title, rating, message, upvote_count, timestamp
            FROM SellerReviews SR 
            WHERE buyer_id = :user_id
            ORDER BY upvote_count DESC
            OFFSET :offset
            LIMIT :num_reviews
        ''',
        user_id=user_id,
        offset=offset,
        num_reviews=num_reviews)

        return [SellerReview(*row) for row in rows]

    @staticmethod
    def get_total_reviews_by_user(user_id):
        rows = app.db.execute(f'''
            SELECT COUNT(*)
            FROM SellerReviews
            WHERE buyer_id = :user_id
        ''', 
        user_id=user_id)

        return rows[0][0]

    @staticmethod
    def get_recent_reviews_by_seller(user_id, offset, num_reviews):
        rows = app.db.execute(f'''
            SELECT  buyer_id, seller_id, title, rating, message, upvote_count, timestamp
            FROM SellerReviews SR JOIN Users U on SR.buyer_id = U.id
            WHERE seller_id = :user_id
            ORDER BY timestamp DESC
            OFFSET :offset
            LIMIT :num_reviews
        ''',
        user_id=user_id,
        offset=offset,
        num_reviews=num_reviews)

        return [SellerReview(*row) for row in rows]
    
    
    @staticmethod
    def get_top_reviews_by_seller(user_id, offset, num_reviews):
        rows = app.db.execute(f'''
            SELECT buyer_id, seller_id, title, rating, message, upvote_count, timestamp
            FROM SellerReviews SR JOIN Users U on SR.buyer_id = U.id
            WHERE seller_id = :user_id
            ORDER BY upvote_count DESC
            OFFSET :offset
            LIMIT :num_reviews
        ''',
        user_id=user_id,
        offset=offset,
        num_reviews=num_reviews)

        return [SellerReview(*row) for row in rows]
    
    @staticmethod
    def get_total_reviews_by_seller(user_id):
        rows = app.db.execute(f'''
            SELECT COUNT(*)
            FROM SellerReviews
            WHERE seller_id = :user_id
        ''', 
        user_id=user_id)

        return rows[0][0]

    @staticmethod
    def get_seller_list(user_id):
        rows = app.db.execute('''
            SELECT CONCAT(firstname, ' ', lastname)
            FROM Users
            WHERE id in (SELECT DISTINCT seller_id
            FROM OrderItem OI JOIN Orders O ON OI.order_id = O.order_id
            WHERE O.buyer_id = :user_id)
        ''', user_id=user_id)

        sellers = [row[0] for row in rows]
        return sellers

    @staticmethod
    def add_review(buyer_id, seller_id, title, rating, message):
        timestamp = datetime.now()

        # Create a dictionary for the review data
        review_data = {
            'buyer_id': buyer_id,
            'seller_id': seller_id,
            'title': title,
            'rating': rating,
            'message': message,
            'upvote_count': 0,
            'timestamp': timestamp
        }

        try:
            # Insert the data into your database
            rows = app.db.execute(f"""
                INSERT INTO SellerReviews (buyer_id, seller_id, title, rating, message, upvote_count, timestamp)
                VALUES (:buyer_id, :seller_id, :title, :rating, :message, 0, :timestamp)
                RETURNING buyer_id, seller_id, title, rating, message, upvote_count, timestamp
            """,
            buyer_id=buyer_id,
            seller_id=seller_id,
            title=title,
            rating=rating,
            message=message,
            timestamp=timestamp)

            return SellerReview(buyer_id, seller_id, title, rating, message, 0, timestamp)
        except Exception as e:
            # Handle the exception or log it as needed
            print(str(e))
            return None

    @staticmethod
    def update_upvote(uid, seller_name, upvote_count):
        app.db.execute(
            '''
            UPDATE SellerReviews
            SET upvote_count = :upvote_count
            WHERE buyer_id = :uid
                AND seller_id = (
        SELECT id
        FROM Users
        WHERE CONCAT(firstname, ' ', lastname) = :seller_name
    )
            ''',
            uid=uid,
            seller_name=seller_name,
            upvote_count=upvote_count
        )
        
        return True

    @staticmethod
    def update_review(seller_id, buyer_id, title, rating, message):
        rows=app.db.execute(f'''
UPDATE SellerReviews
SET
    buyer_id = :buyer_id,
    seller_id =:seller_id,
    title = :title, 
    rating = :rating, 
    message = :message
WHERE
    buyer_id = :buyer_id AND
    seller_id = :seller_id
                ''',
                        buyer_id=buyer_id,
                        seller_id=seller_id,
                        title=title,
                        rating=rating,
                        message=message
            )
        return rows

    @staticmethod
    def delete_review(buyer_id, seller_id):
        rows=app.db.execute(f'''
DELETE FROM SellerReviews
WHERE
                buyer_id = :buyer_id AND
                seller_id = :seller_id;
                            ''',
                        buyer_id=buyer_id,
                        seller_id=seller_id
            )
        return rows

    @staticmethod
    def have_rated_before(uid,current_uid):
        rows = app.db.execute(
            '''
            SELECT *
            FROM SellerReviews
            WHERE buyer_id = :current_uid
                AND seller_id = :uid
            ''',
            uid=uid,
            current_uid=current_uid
        )
        
        return [SellerReview(*row) for row in rows]
    
    @staticmethod
    def average_rating(uid):
        rows = app.db.execute('''
SELECT avg(rating) as avg_rating
            FROM SellerReviews
            WHERE buyer_id = :uid
            GROUP BY buyer_id
''',
                              uid=uid)
        return float(rows[0][0]) if rows else None
    
    @staticmethod
    def average_rating_by_seller(uid):
        rows = app.db.execute('''
SELECT avg(rating) as avg_rating
            FROM SellerReviews
            WHERE seller_id = :uid
            GROUP BY seller_id
''',
                              uid=uid)
        return float(rows[0][0]) if rows else None
