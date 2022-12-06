import pymysql
from flask import current_app, g

def get_db():
    if 'db' not in g:
        g.db = pymysql.connect(host=current_app.config['DATABASE_HOST'],
                       port = current_app.config['DATABASE_PORT'],
                       user=current_app.config['DATABASE_USER'],
                       password=current_app.config['DATABASE_PWD'],
                       db='finstagram',
                       charset='utf8mb4',
                       cursorclass=pymysql.cursors.DictCursor)

    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_app(app):
    app.teardown_appcontext(close_db)