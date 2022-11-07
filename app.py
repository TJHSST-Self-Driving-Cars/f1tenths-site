# app.py
import multiprocessing
import time
import pickle
from flask import Flask, render_template, request, make_response, redirect, url_for
from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)

from oauthlib.oauth2 import WebApplicationClient
import requests

from flask_assets import Bundle, Environment
import simulator.pkg.src.pkg.main as simCode

import json
import os
import sqlite3

from db import init_db_command
from user import User


# Configuration
GOOGLE_CLIENT_ID = "886442690079-alqevh0t0f5vgamvkvnogsm9m33vio1q.apps.googleusercontent.com" #os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = "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" #os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

# Flask app setup
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

assets = Environment(app)
css = Bundle("src/main.css", output="dist/main.css")

assets.register("css", css)
css.build()

# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.unauthorized_handler
def unauthorized():
    return "You must be logged in to access this content.", 403


# Naive database setup
try:
    init_db_command()
except sqlite3.OperationalError:
    # Assume it's already been created
    pass

# OAuth2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)


# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


def simulate(code):
    outL = multiprocessing.Value('d', 0.0)
    process = multiprocessing.Process(target=simCode.testInputDaemon,args=(code,outL))
    process.daemon = True
    process.start()
    
    process.join(50)
    res = outL.value
    if process.is_alive():
        print("Test is hanging!")
        process.terminate()
        print("Terminated!")
        return -1
    return round(res,3)

class Item:
    def __init__(self,name,time):
        self.name=name
        self.time=float(time)
        self.rank=0
    def __repr__(self):
        return self.name+" "+str(self.time)
    def __lt__(self,other):
        return self.time < other.time


def readPlayers():
    try:
        file = open('members.pickle', 'rb')
        o = pickle.load(file)
        return o
    except FileNotFoundError:
        pass
    except EOFError:
        pass
    return []

def writePlayers(items):
    items.sort()
    for i in range(len(items)):
        items[i].rank=i+1
    file = open('members.pickle', 'wb+') 
    pickle.dump(items, file)
    file.close()

def appendPlayer(item):
    l = readPlayers()
    #print("L\n\n",l,"\n\n")
    inTab = False
    for i in range(len(l)):
        if l[i].name==item.name:
            inTab = True
            l[i].time=min(l[i].time,item.time)
    if not inTab:    
        l.append(item)
    writePlayers(l)

@app.route('/leaderboard', methods =["GET", "POST"])
def leaderboard():
    #print("table",readPlayers())
    if current_user.is_authenticated:
        return render_template("leaderboard-logout.html", login_status="", table = readPlayers())
    else:
        return render_template("leaderboard-login.html", login_status="", table = readPlayers())

#https://realpython.com/flask-google-login/
@app.route('/codesubmit', methods =["GET", "POST"])
def codesubmit():

    code = request.form.get("code_")

    result = simulate(simCode.ans)
    #print(result,":D")
    if (result != -1):
        appendPlayer(Item(current_user.name, result)) #log result of the code run
    return render_template("leaderboard-logout.html", run_time=result,  table = readPlayers())

@app.route("/")
def index():
    if current_user.is_authenticated:
        return render_template("codesubmit.html")
    else: 
        return render_template("leaderboard-login.html",table=readPlayers())


@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for login and provide
    # scopes that let you retrieve user's profile from Google
    #print(authorization_endpoint)
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    #print(request_uri)
    return redirect(request_uri)


@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code,
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that we have tokens (yay) let's find and hit URL
    # from Google that gives you user's profile information,
    # including their Google Profile Image and Email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # We want to make sure their email is verified.
    # The user authenticated with Google, authorized our
    # app, and now we've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        return "User email not available or not verified by Google.", 400

    # Create a user in our db with the information provided
    # by Google
    user = User(
        id_=unique_id, name=users_name, email=users_email, profile_pic=picture
    )

    # Doesn't exist? Add to database
    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, picture)

    # Begin user session by logging the user in
    login_user(user)

    # Send user back to homepage
    return redirect(url_for("index"))


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


if __name__ == "__main__":
    app.run(ssl_context="adhoc", debug=True)
