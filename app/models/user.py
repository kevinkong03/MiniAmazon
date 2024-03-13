from flask_login import UserMixin
from flask import current_app as app
from werkzeug.security import generate_password_hash, check_password_hash

from .. import login


class User(UserMixin):
    def __init__(self, id, email, firstname, lastname, address, is_seller):
        self.id = id
        self.email = email
        self.firstname = firstname
        self.lastname = lastname
        self.address = address
        self.is_seller = is_seller

    @staticmethod
    def get_by_auth(email, password):
        rows = app.db.execute("""
SELECT password, id, email, firstname, lastname, address, is_seller
FROM Users
WHERE email = :email
""",
                              email=email)
        if not rows:  # email not found
            return None
        elif not check_password_hash(rows[0][0], password):
            # incorrect password
            return None
        else:
            return User(*(rows[0][1:]))

    @staticmethod
    def get_name(uid):
        rows = app.db.execute("""
SELECT firstname, lastname
FROM Users
WHERE id = :uid
""",
                              uid=uid)
        if not rows:  # email not found
            return None
        else:
            return ({rows[0][0]}, {rows[0][1]})

    @staticmethod
    def email_exists(email):
        rows = app.db.execute("""
SELECT email
FROM Users
WHERE email = :email
""",
                              email=email)
        return len(rows) > 0

    @staticmethod
    def register(email, password, firstname, lastname, address):
        try:
            rows = app.db.execute("""
INSERT INTO Users(email, password, firstname, lastname, address, is_seller)
VALUES(:email, :password, :firstname, :lastname, :address, FALSE)
RETURNING id
""",
                                  email=email,
                                  password=generate_password_hash(password),
                                  firstname=firstname, lastname=lastname,
                                  address=address)
            id = rows[0][0]
            return User.get(id)
        except Exception as e:
            # likely email already in use; better error checking and reporting needed;
            # the following simply prints the error to the console:
            print(str(e))
            return None

    @staticmethod
    @login.user_loader
    def get(id):
        rows = app.db.execute("""
SELECT id, email, firstname, lastname, address, is_seller
FROM Users
WHERE id = :id
""",
                              id=id)
        return User(*(rows[0])) if rows else None

# update user's seller status to be true
    @staticmethod
    def update_is_seller(uid):
        try:
            rows = app.db.execute("""
UPDATE Users
SET is_seller = True
WHERE id = :uid
""",
                                  uid=uid)
            return True
        except Exception as e:
            print(str(e))
            return None
        
    def update_user_information(uid, firstname, lastname, email, address):
            try:
                rows = app.db.execute("""
UPDATE Users
SET firstname = :firstname, lastname = :lastname, email = :email, address = :address
WHERE id = :uid
""",                                                
                                  uid=uid,
                                  firstname=firstname,
                                  lastname=lastname,
                                  email=email,
                                  address=address)
                return True
            except Exception as e:
                print(str(e))
                return None

    def update_user_password(uid, password):
        try:
            rows = app.db.execute("""
UPDATE Users
SET password = :password
WHERE id = :uid
""",
                                  uid=uid,
                                  password=generate_password_hash(password))
            return True
        except Exception as e:
            print(str(e))
            return None