import hashlib
import os
from flask import Blueprint, current_app, redirect, render_template, request, session, url_for
from app.db import get_db

bp = Blueprint("auth", __name__)

@bp.route('/')
def index():
    return render_template('index.html')
    


@bp.route('/login/auth', methods=['POST'])
def login_auth():
    username = request.form['username']
    password = request.form['password']+current_app.config['SALT']
    hashed = hashlib.sha256(password.encode('utf-8')).hexdigest()

    cursor = get_db().cursor()
    query = 'SELECT * FROM person WHERE username=%s and password=%s'
    cursor.execute(query, (username, hashed))
    user = cursor.fetchone()
    cursor.close()

    if(user):
        session['username'] = user['username']
        session['profilePath'] = user['profilePath']
        return redirect(url_for('posts.home', username=username))
    else:
        error = 'Invalid username or password'
        return render_template('auth/login.html', error=error)


@bp.route('/register/auth', methods=['POST'])
def register_auth():
    username = request.form['username']
    password = request.form['password']+current_app['SALT']
    lastName = request.form['lastName']
    firstName = request.form['firstName']
    email = request.form['email']
    hashed = hashlib.sha256(password.encode('utf-8')).hexdigest()
    file_path = os.path.join(current_app.config['IMAGES_DIR'], str(username))

    cursor = get_db().cursor()
    query = 'SELECT * FROM person WHERE username=%s'
    cursor.execute(query, (username))
    user = cursor.fetchone()

    if(user):
        error = "This user already exists"
        return render_template('register.html', error = error)
    else:
        query = 'INSERT INTO person VALUES(%s, %s, %s, %s, %s, %s)'
        cursor.execute(query, (username, hashed, firstName, lastName, email, file_path))
        get_db().commit()
        cursor.close()
        return render_template('index.html')


@bp.route('/logout')
def logout():
    session.pop('username')
    return redirect('/')