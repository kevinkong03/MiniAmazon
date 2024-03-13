from flask import current_app as app


class Category:
    def __init__(self, cid, name, parent_id):
        self.cid = cid
        self.name = name
        self.parent_id = parent_id

    @staticmethod
    def get_all():
        rows = app.db.execute('''
SELECT *
FROM Categories
''',
                              )
        return [Category(*row) for row in rows]

    @staticmethod
    def get_by_cid(cid):
        rows = app.db.execute('''
SELECT *
FROM Categories
WHERE cid = :cid
''',
                              cid=cid)
        return [Category(*row) for row in rows]
    
    @staticmethod
    def get_by_name(name):
        rows = app.db.execute('''
SELECT *
FROM Categories
WHERE name = :name
''',
                              name=name)
        return Category(*(rows[0])) if rows else None

    @staticmethod
    def get_all_parents(cid):
        rows = app.db.execute('''
SELECT c1.cid, c1.name, c1.parent_id
FROM Categories c1, Categories c2
WHERE c1.cid = c2.parent_id AND c2.cid = :cid
''',
                              cid=cid)
        return [Category(*row) for row in rows]

    @staticmethod
    def get_all_children(parent_id):
        rows = app.db.execute('''
SELECT *
FROM Categories
WHERE parent_id=:parent_id
''',
                              parent_id=parent_id)
        return [Category(*row) for row in rows]

    @staticmethod
    def get_cid_by_name(name):
        rows = app.db.execute('''
SELECT cid
FROM Categories
WHERE name = :name
''',
                              name=name)
        return rows[0][0]



