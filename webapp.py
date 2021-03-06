from flask import Flask, redirect, url_for, session, request, jsonify, Markup
from flask_oauthlib.client import OAuth
from flask import render_template, flash
import myEncode as me
from UserHandler import UserHandler
from PostHandler import PostHandler
import pymongo

import pprint
import os
import json
import datetime as dt

app = Flask(__name__)

app.debug = True #Change this to False for production

app.secret_key = os.environ['SECRET_KEY'] #used to sign session cookies
oauth = OAuth(app)
# os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

url = 'mongodb://{}:{}@{}/{}'.format(
    os.environ["MONGO_USERNAME"],
    os.environ["MONGO_PASSWORD"],
    os.environ["MONGO_HOST"],
    os.environ["MONGO_DBNAME"])

client = pymongo.MongoClient(os.environ["MONGO_HOST"])
db = client[os.environ["MONGO_DBNAME"]]
posts_collection = db['posts']
users_collection = db['users']
data_collection = db['other_data']

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

def require_login():
    if "user_data" not in session:
        return True
    return False

@app.context_processor
def inject_logged_in():
    return {"logged_in":('github_token' in session)}

@app.route('/welcome')
def welcome():
    if "do_flash" not in session:
        session["do_flash"] = False
        session["flash_message"] = ""
        session["flash_mode"] = ""

    if session["do_flash"]:
        flash(session["flash_message"],session["flash_mode"])
        session["do_flash"] = False
        session["flash_message"] = ""
        session["flash_mode"] = ""

    return render_template('home.html', posts=renderedPosts, reply_id='x', edit_id="x")

@app.route('/')
def home():
    if require_login(): return redirect(url_for(".login"))

    if "echoCMDS" not in session:
        session["echoCMDS"] = True

    post_handler = PostHandler(posts_collection)
    user_handler = UserHandler(users_collection)

    user_handler.login(session["user_data"]["login"])

    session['user_type'] = 'admin' if user_handler.current.is_admin else 'reg'

    if user_handler.current.ban_level >= 2:
        print("GTFO You Stupid Satan")
        return redirect(url_for(".meme"))

    renderedPosts = post_handler.getRendered(user_handler)

    return render_template('home.html', posts=renderedPosts, reply_id='x', edit_id="x")

@app.route('/newPosts')
def getNewPosts():
    post_handler = PostHandler(posts_collection)
    user_handler = UserHandler(users_collection)

    user_handler.login(session["user_data"]["login"])

    renderedPosts = post_handler.getRendered(user_handler)

    return str(renderedPosts)

@app.route('/posted', methods=['POST'])
def post():
    if require_login(): return redirect(url_for(".login"))

    post_handler = PostHandler(posts_collection)
    user_handler = UserHandler(users_collection)

    user_handler.login(session["user_data"]["login"])

    if user_handler.current.ban_level >= 2:
        return redirect(url_for(".home"))

    msg = request.form['message']

    if str(msg).startswith("#!"):
        cmds = msg.split(' ')

        if not user_handler.current.is_admin:
            msg = "$$This noob tried to use an admin command$$"

        elif cmds[1] == "ban":
            id = int(cmds[2])
            usr = user_handler.usrFor(id)
            level = int(cmds[3])
            usr.ban_level = level
            msg = "$$Set ban level for %s to %i$$" % (usr.name, level)

        elif cmds[1] == "unban":
            id = int(cmds[2])
            usr = user_handler.usrFor(id)
            usr.ban_level = 0
            msg = "$$Unbanned %s (%i)$$" % (usr.name, id)

        elif cmds[1] == "makeadmin":
            id = int(cmds[2])
            user_handler.makeAdmin(id)
            usr = user_handler.usrFor(id)
            msg = "$$Made %s an Admin$$" % (usr.name)

        elif cmds[1] == "noadmin":
            id = int(cmds[2])
            user_handler.unAdmin(id)
            usr = user_handler.usrFor(id)
            msg = "$$Revoked Admin privileges from %s$$" % (usr.name)

        elif cmds[1] == "toggleecho":
            session["echoCMDS"] = not session["echoCMDS"]
            msg = "$$Toggle command echo$$"

        elif cmds[1] == "clearforum":
            post_handler.clear()
            msg = "$$Cleared Forum$$"

        elif cmds[1] == "lookat":
            if cmds[2] == "post":
                id = int(cmds[3])
                post = post_handler.postFor(id)
                msg = post.rep()

            elif cmds[2] == "user":
                nm = cmds[3]
                user = user_handler.usrForName(nm)
                msg = user.rep()

        if not session["echoCMDS"]:
            return redirect(url_for(".home"))

    with open("static/badWords.json") as bwFile:
        rawbw = bwFile.read()
    decd = me.decode(rawbw)
    bad_words = json.loads(decd)

    for word in msg.split(" "):
        if word.lower() in bad_words:
            msg = "$$This user is a horrible person and shall henceforth be known as \"Spawn of Satan\"$$"
            user_handler.banCurrent()

    if request.form['replyID'] == 'x' and request.form['editID'] == 'x':
        post_handler.post(msg, user_handler.current)

    elif not request.form['editID'] == 'x':
        post_handler.editPost(request.form['editID'], msg)

    else:
        post_handler.postReply(msg, user_handler.current, request.form['replyID'])

    return redirect(url_for(".home"))

@app.route('/deletePost', methods=['POST'])
def deletePost():
    if require_login(): return redirect(url_for(".login"))

    post_handler = PostHandler(posts_collection)
    user_handler = UserHandler(users_collection)

    user_handler.login(session["user_data"]["login"])

    if user_handler.current.ban_level >= 2:
        return redirect(url_for(".home"))

    post_handler.deletePost(request.form['msgID'])

    return redirect(url_for(".home"))

@app.route('/editPost', methods=['POST'])
def editPost():
    if require_login(): return redirect(url_for(".login"))

    msgID = request.form['msgID']

    post_handler = PostHandler(posts_collection)
    user_handler = UserHandler(users_collection)

    user_handler.login(session["user_data"]["login"])

    if user_handler.current.ban_level >= 2:
        return redirect(url_for(".home"))

    posto = post_handler.postFor(msgID)
    if posto not in post_handler.posts:
        return redirect(url_for(".home"))

    message = posto.message
    renderedPosts = post_handler.getRendered(user_handler)

    session['user_type'] = 'admin' if user_handler.current.is_admin else 'reg'

    return render_template('home.html', posts=renderedPosts, edit_id=msgID, reply_id='x', message=message)

@app.route('/replyPost', methods=['POST'])
def replyPost():
    if require_login(): return redirect(url_for(".login"))

    post_handler = PostHandler(posts_collection)
    user_handler = UserHandler(users_collection)

    user_handler.login(session["user_data"]["login"])

    if user_handler.current.ban_level >= 2:
        return redirect(url_for(".home"))

    renderedPosts = post_handler.getRendered(user_handler)

    session['user_type'] = 'admin' if user_handler.current.is_admin else 'reg'

    return render_template('home.html', posts=renderedPosts, reply_id=request.form['msgID'], edit_id='x')

#redirect to GitHub's OAuth page and confirm callback URL
@app.route('/login')
def login():
    return github.authorize(callback=url_for('authorized', _external=True, _scheme='https')) #callback URL must match the pre-configured callback URL

@app.route('/logout')
def logout():
    session.clear()
    session["do_flash"] = True
    session["flash_message"] = "You were logged out"
    session["flash_mode"] = "warning"
    return redirect(url_for(".welcome"))

@app.route('/login/authorized')
def authorized():
    resp = github.authorized_response()
    if resp is None:
        session.clear()
        message = 'Access denied: reason=' + request.args['error'] + ' error=' + request.args['error_description'] + ' full=' + pprint.pformat(request.args)
        session["do_flash"] = True
        session["flash_message"] = message
        session["flash_mode"] = "warning"
        return redirect(url_for(".welcome"))
    else:
        try:
            session['github_token'] = (resp['access_token'], '') #save the token to prove that the user logged in
            session['user_data']=github.get('user').data
            message='You were successfully logged in as ' + session['user_data']['login']
        except Exception as inst:
            session.clear()
            print(inst)
            message='Unable to login, please try again.  '
            session["do_flash"] = True
            session["flash_message"] = message
            session["flash_mode"] = "danger"
            return redirect(url_for(".welcome"))

    # post_handler = PostHandler(posts_collection)
    user_handler = UserHandler(users_collection)

    if not user_handler.has(session["user_data"]["login"]):
        user_handler.newUsr(session["user_data"]["login"])
    else:
        user_handler.login(session["user_data"]["login"])

    return redirect(url_for(".home"))

@app.route('/reprimand', methods=['GET','POST'])
def reprimand():
    return render_template("meme.html")

@app.route('/meme')
def meme():
    return render_template("meme.html")

@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')


if __name__ == '__main__':
    app.run(debug=True, host="localhost", port=5000)
