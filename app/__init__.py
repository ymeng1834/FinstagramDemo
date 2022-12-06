from flask import Flask, current_app

def create_app():
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_pyfile('config.py', silent=True)

    from app import db, auth, posts, people
    
    db.init_app(app)

    app.register_blueprint(auth.bp)
    app.register_blueprint(posts.bp)
    app.register_blueprint(people.bp)

    app.add_url_rule("/", endpoint="index")

    return app