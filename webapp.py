from flask import Flask, redirect, url_for, session, request, jsonify, Markup
from flask_oauthlib.client import OAuth
from flask import render_template
import myEncode as me

import pprint
import os
import json
import datetime

app = Flask(__name__)

app.debug = True #Change this to False for production

app.secret_key = os.environ['SECRET_KEY'] #used to sign session cookies
oauth = OAuth(app)
# os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

admins = os.environ['admins']

#Set up GitHub as OAuth provider
github = oauth.remote_app(
    'github',
    consumer_key=os.environ['GITHUB_CLIENT_ID'], #your web app's "username" for github's OAuth
    consumer_secret=os.environ['GITHUB_CLIENT_SECRET'],#your web app's "password" for github's OAuth
    request_token_params={'scope': 'user:email'}, #request read-only access to the user's email.  For a list of possible scopes, see developer.github.com/apps/building-oauth-apps/scopes-for-oauth-apps
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize' #URL for github's OAuth login
)

#use a JSON file to store the past posts.  A global list variable doesn't work when handling multiple requests coming in and being handled on different threads
#Create and set a global variable for the name of you JSON file here.  The file will be created on Heroku, so you don't need to make it in GitHub

def require_login():
    if "user_data" not in session:
        return True
    return False

def get_post(id, posts):
    for p in posts:
        # print(type(p['id']))
        if p['id'] == int(id): return p

    return None

def get_children(parentID, posts):
    out = []

    for p in posts:
        if 'parents' not in p: continue
        if int(parentID) in p['parents']:
            out.append(p)

    return out

def generateID(key1, key2):
    return hash(key1 + key2)

@app.context_processor
def inject_logged_in():
    return {"logged_in":('github_token' in session)}

@app.route('/')
def home():
    if require_login(): return redirect(url_for(".login"))

    session["user_type"] = "admin" if session['user_data']['login'] in admins else "regular"

    warned = False

    if user_banned(session['user_data']['login']) == "B":
        redirect("https://answers.yahoo.com/question/index?qid=20190217173954AAszYW0")

    with open("static/posts.json") as inFile:
        posts = json.load(inFile)

    del posts[0]
    # print(posts)

    return render_template('home.html', posts=posts, reply_id='x', edit_id="x", warned=warned)

@app.route('/posted', methods=['POST'])
def post():
    if require_login(): return redirect(url_for(".login"))

    with open("static/posts.json") as inFile:
        posts = json.load(inFile)

    msg = request.form['message']
    sender = session["user_data"]["login"]
    theTime = datetime.datetime.now().strftime("%m/%d %H:%M:%S")

    if request.form['replyID'] == 'x' and request.form['editID'] == 'x':
        if user_banned(session['user_data']['login']) == "W":
            theDict = {"message":msg, "sender":sender, "time":theTime, "id":generateID(sender,theTime), 'level':0, "parents": [], "bad_guy":True}
        else:
            theDict = {"message":msg, "sender":sender, "time":theTime, "id":generateID(sender,theTime), 'level':0, "parents": [], "bad_guy":False}

        with open("static/badWords.json") as fitfile:
            raw = fitfile.read()
            decd = me.decode(raw)
            bad_words = json.loads(decd)

        for word in msg.split(" "):
            if word.lower() in bad_words:
                theDict = {"message":"<<This user is a horrible person and shall henceforth be known as \"Spawn of Satan\">>", "sender":sender, "time":theTime, "id":generateID(sender,theTime), 'level':0, "parents": [], "bad_guy":True}
                ban_user(sender)

        posts.append(theDict)

    elif not request.form['editID'] == 'x':
        oldPost = get_post(request.form['editID'], posts)
        ind = posts.index(oldPost)
        oldPost["message"] = msg
        oldPost["editTime"] = "Edited: \n%s" % theTime
        posts[ind] = oldPost

    else:
        print(request.form['replyID'])
        parent = get_post(request.form['replyID'],posts)
        other_parents = parent['parents']
        other_parents.append(parent['id'])
        new_id = generateID(sender, theTime)
        repDict = {"message":msg, "sender":sender, "time":theTime, "id":new_id, 'level':parent['level']+1, "parents": other_parents, "bad_guy":False}
        new_index = posts.index(parent) + len(get_children(parent['id'],posts))
        posts.insert(new_index,repDict)

    with open("static/posts.json", 'w') as outFile:
        json.dump(posts, outFile)

    return redirect(url_for(".home"))

@app.route('/deletePost', methods=['POST'])
def deletePost():
    if require_login(): return redirect(url_for(".login"))

    with open("static/posts.json") as inFile:
        posts = json.load(inFile)

    del posts[0]

    msg = request.form['msgID']

    post = get_post(msg, posts)
    posts.remove(post)

    for p in get_children(msg, posts):
        posts.remove(p)

    posts.insert(0, {"is_test":True, "id":0})

    with open("static/posts.json", 'w') as outFile:
        json.dump(posts, outFile)

    return redirect(url_for(".home"))

@app.route('/editPost', methods=['POST'])
def editPost():
    if require_login(): return redirect(url_for(".login"))

    with open("static/posts.json") as inFile:
        posts = json.load(inFile)

    msg = request.form['msgID']
    message = get_post(msg, posts)["message"]

    del posts[0]

    return render_template('home.html', posts=posts, edit_id=msg, reply_id='x', message=message)

@app.route('/replyPost', methods=['POST'])
def replyPost():
    if require_login(): return redirect(url_for(".login"))

    with open("static/posts.json") as inFile:
        posts = json.load(inFile)

    del posts[0]

    return render_template('home.html', posts=posts, reply_id=request.form['msgID'], edit_id='x')

#redirect to GitHub's OAuth page and confirm callback URL
@app.route('/login')
def login():
    return github.authorize(callback=url_for('authorized', _external=True, _scheme='https')) #callback URL must match the pre-configured callback URL

@app.route('/logout')
def logout():
    session.clear()
    return render_template('message.html', message='You were logged out')

@app.route('/login/authorized')
def authorized():
    resp = github.authorized_response()
    if resp is None:
        session.clear()
        message = 'Access denied: reason=' + request.args['error'] + ' error=' + request.args['error_description'] + ' full=' + pprint.pformat(request.args)
        return render_template('message.html', message=message)
    else:
        try:
            session['github_token'] = (resp['access_token'], '') #save the token to prove that the user logged in
            session['user_data']=github.get('user').data
            message='You were successfully logged in as ' + session['user_data']['login']
        except Exception as inst:
            session.clear()
            print(inst)
            message='Unable to login, please try again.  '
            return render_template('message.html', message=message)
    return redirect(url_for(".home"))

#the tokengetter is automatically called to check who is logged in.
@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')

def user_banned(user):
    with open("static/banned.json") as banFile:
        banned = json.load(banFile)

    for ban in banned:
        if ban["username"] == user and ban["ban-level"] == 2: return "B"
        elif ban["username"] == user and ban["ban-level"] == 1: return "W"

    return "A"

def ban_user(user):
    with open("static/banned.json") as banFile:
        banned = json.load(banFile)

    for ban in banned:
        if ban["username"] == user:
            ban["ban-level"] = 2
            return

    banned.append({"username":user, "ban-level":1, "ban-time":datetime.datetime.now().strftime("%m/%d %H:%M:%S")})

    with open("static/banned.json", 'w') as banFile2:
        json.dump(banned,banFile2)

if __name__ == '__main__':
    app.run(debug=True, host="localhost", port=5000)
