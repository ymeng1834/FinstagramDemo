from flask import Blueprint, redirect, request, session, url_for
from app.db import get_db


bp = Blueprint("people",__name__)

@bp.route('/follow', methods=['POST'])
def add_follow():
    curr = session['username']
    username = request.form['follow']
    cursor = get_db().cursor()
    query = "INSERT INTO Follow (follower, followee, followStatus) VALUES (%s, %s, 0)"
    cursor.execute(query, (curr, username))
    get_db().commit()
    cursor.close()

    return redirect(url_for('posts.get_user_profile', username=username))