import datetime
from flask import Blueprint, redirect, render_template, request, session, url_for
from app.db import get_db


bp = Blueprint("posts",__name__,template_folder='templates/posts')

availablePosts = '''
CREATE TEMPORARY TABLE availablePosts
    SELECT username, profilePath, pID, filePath, caption, postingDate
    FROM (
        (
            SELECT p.pID, p.postingDate, p.filePath, p.caption, p.poster
        	FROM Photo p JOIN Follow f ON p.poster = f.followee
        	WHERE f.follower=%s AND f.followStatus=1 AND p.allFollowers=1
        )
        UNION 
        (
            SELECT p.pID, p.postingDate, p.filePath, p.caption, p.poster
            FROM (
                SELECT f1.followee AS user
                FROM Follow f1 JOIN Follow f2 ON f1.follower=f2.followee AND f1.followee=f2.follower
                WHERE f1.follower=%s
                ) mutual JOIN Photo p ON mutual.user=p.poster
            WHERE allMutuals=1
        )
        UNION
        (
            SELECT p.pID, p.postingDate, p.filePath, p.caption, p.poster
            FROM BelongTo bt NATURAL JOIN SharedWith sw NATURAL JOIN Photo p
            WHERE bt.username=%s
        )
    ) tb JOIN Person p ON tb.poster=p.username;
'''


@bp.route('/<username>')
@bp.route('/<username>/<option>')
@bp.route('/<username>/<option>/<group>')
def home(username, option='following', group='Group'):
    user = session['username']
    cursor = get_db().cursor()

    query = 'SELECT groupName FROM FriendGroup WHERE groupCreator=%s'
    cursor.execute(query, (user))
    groups = cursor.fetchall()

    cursor.execute(availablePosts, (user, user, user))

    if option=='following':
        query = 'SELECT * FROM availablePosts ORDER BY postingDate DESC'
        cursor.execute(query)
        posts = cursor.fetchall()
    elif option=='mutuals':
        query = '''
        SELECT username, profilePath, pID, filePath, caption, postingDate
        FROM Follow f1 JOIN Follow f2 ON (f1.follower=f2.followee AND f1.followee=f2.follower) 
        JOIN availablePosts p ON f1.followee=p.username
        WHERE f1.follower=%s
        ORDER BY postingDate DESC
        '''
        cursor.execute(query, (user))
        posts = cursor.fetchall()
    elif option=='group':
        query = '''
        SELECT username, profilePath, pID, filePath, caption, postingDate
        FROM BelongTo JOIN availablePosts USING (username)
        WHERE groupName=%s AND groupCreator=%s
        ORDER BY postingDate DESC
        '''
        cursor.execute(query, (group, user))
        posts = cursor.fetchall()
    else:
        posts = 'error'

    cursor.close()
    
    return render_template('home.html', user=user, posts=posts, groups=groups, option=option, group=group)


@bp.route('/post/<pid>')
def post_details(pid):
    def get_time(dt):
        diff = datetime.datetime.now() - dt
        if diff.total_seconds() < 120:
            res = 'just now'
        elif diff.total_seconds() < 3599:
            res = str(int(diff.total_seconds()/60))+'m ago'
        elif diff.total_seconds() < 86399:
            res = str(int(diff.total_seconds()/3600))+'h ago'
        else:
            res = str(diff.days)+'d ago'
        return res

    cursor = get_db().cursor()

    query = '''
    SELECT username, firstName, lastName, profilePath, pID, filePath, caption, postingDate
    FROM Photo pt JOIN Person p ON pt.poster=p.username
    WHERE pID=%s
    '''
    cursor.execute(query, (pid))
    basic_info = cursor.fetchone()
    basic_info['postingDate'] = get_time(basic_info['postingDate'])

    query = '''
    SELECT username, profilePath, reactionTime, comment
    FROM ReactTo JOIN Person USING (username)
    WHERE pID=%s
    ORDER BY reactionTime DESC
    '''
    cursor.execute(query, (pid))
    reactions = cursor.fetchall()
    for r in reactions:
        r['reactionTime'] = get_time(r['reactionTime'])

    query = '''
    SELECT username, profilePath, firstName, lastName
    FROM Tag JOIN Person USING (username)
    WHERE pID=%s AND tagStatus=1
    ORDER BY username
    '''
    cursor.execute(query, (pid))
    tagged_people = cursor.fetchall()
    cursor.close()

    return render_template('details.html', basic=basic_info, reactions=reactions, tagged=tagged_people)


@bp.route('/post/update', methods=['POST'])
def update_post():
    user = session['username']
    pid = request.form['pid']
    comment = request.form['comment']
    reactionTime = str(datetime.datetime.now())

    cursor = get_db().cursor()
    query = "INSERT INTO ReactTo(username, pID, reactionTime, comment) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (user, pid, reactionTime, comment))
    get_db().commit()
    cursor.close()
    
    return redirect(url_for('.post_details', pid=pid))

@bp.route('/user/<username>')
@bp.route('/user/<username>/<option>')
def get_user_profile(username, option='posts'):
    curr = session['username']
    cursor = get_db().cursor()

    query = 'SELECT username, firstName, lastName, profilePath FROM Person WHERE username=%s'
    cursor.execute(query, (username))
    profile = cursor.fetchone()

    query = 'SELECT * FROM Follow WHERE follower=%s AND followee=%s AND followStatus=1'
    cursor.execute(query, (curr, username))
    followed = cursor.fetchone()

    query = 'SELECT COUNT(*) count FROM Follow WHERE follower=%s AND followStatus=1'
    cursor.execute(query, (username))
    followings = cursor.fetchone()

    query = 'SELECT COUNT(*) count FROM Follow WHERE followee=%s AND followStatus=1'
    cursor.execute(query, (username))
    followers = cursor.fetchone()

    query = '''
    SELECT f1.followee username
    FROM Follow f1 JOIN Follow f2 ON f1.followee=f2.follower
    WHERE f1.follower=%s AND f2.followee=%s AND f1.followStatus=1 AND f2.followStatus=1
    '''
    cursor.execute(query, (curr, username))
    common = cursor.fetchall()
    if len(common) > 2:
        common = {'one':common[0]['username'], 'two':common[1]['username'], 'count':len(common)-2}

    cursor.execute(availablePosts, (curr, curr, curr))

    if option=='posts':
        query = 'SELECT * FROM availablePosts WHERE username=%s ORDER BY postingDate DESC'
    elif option=='tagged':
        query = '''
        SELECT p.pID, p.postingDate, p.filePath, p.username, p.profilePath
        FROM Tag t JOIN availablePosts p ON t.pID=p.pID
        WHERE t.username=%s AND t.tagStatus=1
        ORDER BY p.postingDate DESC
        '''
    elif option=='commented':
        query = '''
        SELECT p.pID, p.postingDate, p.filePath, p.profilePath, p.username, r.reactionTime, r.comment
        FROM ReactTo r JOIN availablePosts p ON r.pID=p.pID
        WHERE r.username=%s
        ORDER BY r.reactionTime DESC
        '''
    cursor.execute(query,(username))
    posts = cursor.fetchall()
    cursor.close()

    return render_template('profile.html', profile=profile, followed=followed, common=common, fg_count=followings, fr_count=followers, posts=posts, option=option)




