import os
import numpy as np
import pandas as pd
import numpy as np
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from cs50 import SQL
from functools import wraps
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import date

app = Flask(__name__)

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///data.db")

""" functions """

def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code

def addMHRecord(aspect):
    today = date.today()
    data = db.execute("SELECT * FROM health WHERE user_ID = :id AND date = :date", id=session["user_id"], date=today)
    score = 0
    print (today)
    print (data)
    # Get values from webpage form then calculate scores then enter scores to db
    if aspect == "self_esteem":
        for i in range(1,11):
        # Check to see if what user entered be converted to int. If not it means user has not given an answer.
            try:
                hmm = int(request.form.get(str(i)))
            except:
                return 1
        # Calculate score
            score += hmm
    else:
        for i in range(1,9):
            # Check to see if what user entered be converted to int. If not it means user has not given an answer.
            try:
                hmm = int(request.form.get(str(i)))
            except:
                return 1
            # Calculate score
            score += hmm
    # Add to db
    if data == []:
        db.execute("INSERT INTO health (user_ID, :aspect ) VALUES (:id,:score)", aspect=aspect, id=session["user_id"], score=score)
    else: # if entry for today's date exists, then update that entry
        db.execute("UPDATE health SET :aspect = :score WHERE user_id = :id AND date = :date ", aspect=aspect, score=score,id=session["user_id"], date = today)

"""" flask routes """

@app.route("/")
@login_required
def home():
    # Display a summary of user's data
    username = db.execute("SELECT username FROM users WHERE user_ID = :id", id=session["user_id"])
    fields = db.execute("PRAGMA table_info(usage)")
    return render_template("home.html", username=username[0]["username"])

@app.route("/login", methods=["GET", "POST"])
def login():
    """ Log user in"""
    # logout old user
    session.clear()

    if request.method == "POST":

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 402)

        # Remember which user has logged in
        session["user_id"] = rows[0]["user_ID"]

        return redirect("/")

    else:
        return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    # register the user
    if request.method == "POST":
        # check username not already registered
        username = request.form.get("username")
        users = db.execute("SELECT username FROM users")
        for user in users:
            if user["username"] == username:
                return apology("Username already exists")

        # Store a hash of the password
        hash = generate_password_hash(request.form.get("password"))

        # Store username and hash into database
        db.execute("INSERT INTO users (username, hash, gender) VALUES(:username, :hash, :gender)", username=username, hash=hash,gender=request.form.get("gender"))

        # redirect to login page
        return redirect("/login")
    else:
        return render_template("register.html")

@app.route("/health", methods=["GET"])
@login_required
def health():
        return render_template("health.html")

@app.route("/depression", methods=["GET", "POST"])
@login_required
def depression():
    if request.method == "POST":
        if addMHRecord("depression") == 1:
            return apology("Please answer all questions!", 405)

        return redirect("/anxiety")
    else:
        return render_template("depression.html")

@app.route("/anxiety", methods=["GET", "POST"])
@login_required
def anxiety():
    if request.method == "POST":
        if addMHRecord("anxiety") == 1:
            return apology("Please answer all questions!", 405)
        return redirect("/sleep")
    else:
        return render_template("anxiety.html")

@app.route("/sleep", methods=["GET", "POST"])
@login_required
def sleep():
    if request.method == "POST":
        if addMHRecord("sleep") == 1:
            return apology("Please answer all questions!", 405)
        return redirect("/esteem")
    else:
        return render_template("sleep.html")

@app.route("/esteem", methods=["GET", "POST"])
@login_required
def esteem():
    if request.method == "POST":
        if addMHRecord("self_esteem") == 1:
            return apology("Please answer all questions!", 405)
        return redirect("/")
    else:
        return render_template("esteem.html")

@app.route("/phone", methods=["GET", "POST"])
@login_required
def phone():
    if request.method == "POST":
        app = request.form.get("app")
        other = request.form.get("other")
        time = request.form.get("minutes")
        today = date.today()
        data = db.execute("SELECT * FROM usage WHERE user_ID = :id AND date = :date", id=session["user_id"], date=today)
        # If user selects 'other' then load new webpage where they can type in the name of the app
        if app == "other":
            return render_template("other.html")
        if not app :
            try:
                db.execute("ALTER TABLE usage ADD :other integer", other=other.lower())
            except:
                print("app name exists")
            app = other
        # If no entries for today's date, create new entry and add minutes
        app = app.lower()
        if data == []:
            db.execute("INSERT INTO usage (user_ID, :name) VALUES (:id,:time)", name=app, id=session["user_id"], time=time)
        else: # if entry for today's date exists, then update that entry
            db.execute("UPDATE usage SET :app = :time WHERE user_id = :id AND date = :date ", app=app, time=time,id=session["user_id"], date = today)
        return render_template("phone.html")

    else:
        return render_template("phone.html")

@app.route("/stats", methods=["GET"])
@login_required
def analyse():
    """ grab data from database and perform data analysis """
    health = db.execute("SELECT * FROM health WHERE user_ID = :id", id=session["user_id"])
    phone = db.execute("SELECT * FROM usage WHERE user_ID = :id", id=session["user_id"])
    hdata = []
    pdata = []
    # get relevant values for health data then put values into two array
    for i in range(3):
        health1 = [health[i][h] for h in health[i]]
        hdata.append(health1[2:6])
    hdata = np.array(hdata)
    hdata[[0, 2]] = hdata[[2, 0]]
    print(np.mean(hdata, axis = 0))
    print(np.std(hdata, axis = 0))
    print(np.median(hdata, axis = 0))

    # get relevant values for phone data then put values into 2D array
    for i in range(3):
        phone1 = [phone[i][h] for h in phone[i]]
        pdata.append(phone1[2:7] + phone1[9:14])
    pdata = np.array(pdata)
    red = pdata[...,2]
    dep = []
    print(red)
    for i in hdata[...,0]:
        dep.append(int(i))
    dep = np.array(dep)
    print(dep)
    # pearson
    print (np.corrcoef(red, dep ))



    return render_template("stats.html",)

@app.route("/info")
def info():
    return render_template("info.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")
