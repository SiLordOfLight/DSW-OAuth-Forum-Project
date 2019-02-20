from flask import Flask, redirect, url_for, session, request, jsonify, Markup
from flask_oauthlib.client import OAuth
from flask import render_template
import myEncode as me
from UserHandler import UserHandler
from PostHandler import PostHandler

import pprint
import os
import json
import datetime

app = Flask(__name__)

app.debug = True #Change this to False for production

app.secret_key = os.environ['SECRET_KEY'] #used to sign session cookies
oauth = OAuth(app)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

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

def require_login():
    if "user_data" not in session:
        return True
    return False

@app.context_processor
def inject_logged_in():
    return {"logged_in":('github_token' in session)}

@app.route('/')
def home():
    if require_login(): return redirect(url_for(".login"))

    post_handler = PostHandler()
    user_handler = UserHandler(admins)

    user_handler.login(session["user_data"]["login"])

    if user_handler.current.ban_level == 2:
        print("GTFO You Stupid Satan")
        return redirect(url_for(".meme"))

    renderedPosts = post_handler.getRendered(user_handler)

    post_handler.close()
    user_handler.close()

    return render_template('home.html', posts=renderedPosts, reply_id='x', edit_id="x")

@app.route('/posted', methods=['POST'])
def post():
    if require_login(): return redirect(url_for(".login"))


    post_handler = PostHandler()
    user_handler = UserHandler(admins)

    user_handler.login(session["user_data"]["login"])

    msg = request.form['message']

    with open("static/badWords.json") as fitfile:
        raw = fitfile.read()
        decd = me.decode(raw)
        bad_words = json.loads(decd)

    for word in msg.split(" "):
        if word.lower() in bad_words:
            msg = "<<This user is a horrible person and shall henceforth be known as \"Spawn of Satan\">>"
            user_handler.banCurrent()

    if request.form['replyID'] == 'x' and request.form['editID'] == 'x':
        post_handler.post(msg, user_handler.current)

    elif not request.form['editID'] == 'x':
        post_handler.editPost(request.form['editID'], msg)

    else:
        post_handler.postReply(msg, user_handler.current, request.form['replyID'])

    post_handler.close()
    user_handler.close()

    return redirect(url_for(".home"))

@app.route('/deletePost', methods=['POST'])
def deletePost():
    if require_login(): return redirect(url_for(".login"))

    post_handler = PostHandler()
    # user_handler = UserHandler(admins)

    # user_handler.login(session["user_data"]["login"])

    # user_handler.current.deleted()

    post_handler.deletePost(request.form['msgID'])
    post_handler.close()

    post_handler.close()
    # user_handler.close()

    return redirect(url_for(".home"))

@app.route('/editPost', methods=['POST'])
def editPost():
    if require_login(): return redirect(url_for(".login"))

    msgID = request.form['msgID']

    post_handler = PostHandler()
    user_handler = UserHandler(admins)

    user_handler.login(session["user_data"]["login"])

    message = post_handler.postFor(msgID).message
    renderedPosts = post_handler.getRendered(user_handler)

    post_handler.close()
    user_handler.close()

    return render_template('home.html', posts=renderedPosts, edit_id=msgID, reply_id='x', message=message)

@app.route('/replyPost', methods=['POST'])
def replyPost():
    if require_login(): return redirect(url_for(".login"))

    post_handler = PostHandler()
    user_handler = UserHandler(admins)

    user_handler.login(session["user_data"]["login"])

    renderedPosts = post_handler.getRendered(user_handler)

    post_handler.close()
    user_handler.close()

    return render_template('home.html', posts=renderedPosts, reply_id=request.form['msgID'], edit_id='x')

#redirect to GitHub's OAuth page and confirm callback URL
@app.route('/login')
def login():
    return github.authorize(callback=url_for('authorized', _external=True, _scheme='http')) #callback URL must match the pre-configured callback URL

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

    # post_handler = PostHandler()
    user_handler = UserHandler(admins)

    if not user_handler.has(session["user_data"]["login"]):
        user_handler.newUsr(session["user_data"]["login"])
    else:
        user_handler.login(session["user_data"]["login"])

    # post_handler.close()
    user_handler.close()

    return redirect(url_for(".home"))

@app.route('/reprimand')
def reprimand():
    return render_template("reprimand.html")

@app.route('/meme')
def meme():
    return render_template("meme.html")
#the tokengetter is automatically called to check who is logged in.
@github.tokengetter
def get_github_oauth_token():
    return session.get('github_token')


if __name__ == '__main__':
    app.run(debug=True, host="localhost", port=5000)
