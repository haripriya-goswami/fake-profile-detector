from flask import Flask, redirect, url_for, render_template, request, session
from flask_pymongo import PyMongo
from fuzzywuzzy import process, fuzz
import pandas as pd
from fuzzy import match
from datetime import timedelta
import os.path

app = Flask(__name__)
app.secret_key = "hello"
app.config["MONGO_URI"] = "mongodb://localhost:27017/FPD"
app.permanent_session_lifetime = timedelta(days=2)

data = PyMongo(app).db.data

path = "/home/dinky/Documents/fake-profile-detector/static/images/"


@app.route("/", methods=["POST", "GET"])
def login():
    if "username" in session:
        return redirect(url_for("index"))
    elif request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if(len(list(data.find({"username": username, "password": int(password)})))):
            session.permanent = True
            session["username"] = username

            image = f"/static/images/{session['username']}.jpg" if os.path.exists(
                f"{path}{session['username']}.jpg") else "/static/images/no.jpg"

            if(list(data.find({"username": username}))[0]['is_suspended']):
                return render_template('suspended.html', pic=image, hrf="/logout")

            return redirect(url_for("index"))

        return render_template('login.html', err=1)

    return render_template("login.html")


@app.route("/home")
def index():
    if "username" in session:
        image = f"/static/images/{session['username']}.jpg" if os.path.exists(
            f"{path}{session['username']}.jpg") else "/static/images/no.jpg"

        if(list(data.find({"username": session['username']}))[0]['is_suspended']):
            return render_template('suspended.html', pic=image, hrf="/logout")

        res = match(session['username'])

        if(res != 'No response'):
            return render_template(
                "index.html",
                name=session["username"],
                pic=image,
                fake=list(data.find({'username': session['username']}))[
                    0]['is_fake'],
                matches=res,
                posts=data.find({"username": session['username']})[
                    0]["posts"],
                friends_count=data.find({"username": session['username']})[
                    0]["friends_count"],
                hrf="/logout"
            )

    return render_template("login.html")


@app.route("/changed", methods=['POST'])
def changed():
    if request.method == "POST":
        image = f"/static/images/{session['username']}.jpg" if os.path.exists(
            f"{path}{session['username']}.jpg") else "/static/images/no.jpg"

        detail = list(
            dict(list(data.find({"username": session['username']}))[0]).values())[1:]
        ref = list(
            dict(list(data.find({"username": detail[24]}))[0]).values())[1:]

        un = request.form['username']
        un_percent = fuzz.ratio(un, ref[0])

        fn = request.form['fullname']
        fn_percent = fuzz.ratio(fn, ref[1])

        dsc = request.form['description']
        dsc_percent = fuzz.ratio(dsc, ref[2])

        if(un_percent > 75 or fn_percent > 75 or dsc_percent > 75):
            return render_template('suspended.html', pic=image, err=1, hrf="/logout")

        data.update_one({"username": session['username']}, {"$set": {
                        "username": un, "fullname": fn, "description": dsc, "reports": 0, "is_suspended": 0, "refers": ""}}, upsert=False, array_filters=[])

        session['username'] = un

        return redirect(url_for('index'))

    return render_template('suspended.html', pic=image, hrf="/logout")


@app.route("/logout")
def logout():
    if "username" in session:
        session.pop("username", None)
    return redirect(url_for("login"))


@app.route("/report/<name>", methods=["POST", "GET"])
def report(name):
    if request.method == "POST":
        person = request.form['person']
        usrname = request.form['usrname'] if person == 'Someone' else session['username']

        rep = list(data.find({'username': name}))[0]['reports']
        data.update({'username': name}, {"$set": {"reports": rep+1}})
        if(rep+1 >= 15):
            data.update_one({'username': name}, {
                "$set": {"is_suspended": 1, "refers": usrname}}, upsert=False, array_filters=[])
    return redirect(url_for("index"))


@app.route("/search", methods=["POST", "GET"])
def search():
    if request.method == "POST":
        image = f"/static/images/{session['username']}.jpg" if os.path.exists(
            f"{path}{session['username']}.jpg") else "/static/images/no.jpg"
        uname = request.form["uname"]
        unames = [i['username'] for i in list(
            data.aggregate([{"$project": {"username": 1, "_id": 0}}]))]
        res = process.extract(uname, unames)
        rnames = [i[0] for i in res]
        rdata = list((k[0], data.find(
            {"username": k[0]})[0]['is_fake']) for k in res)
        images = [i for i in rnames if os.path.exists(f"{path}{i}.jpg")]
        return render_template("list.html", users=rdata, img=images, name=uname, pic=image, hrf="/logout")


@app.route("/profile/<name>")
def profile(name):
    detail = list(
        dict(list(data.find({"username": name}))[0]).values())[1:]

    result = []
    prim = 0

    image = f"/static/images/{name}.jpg" if os.path.exists(
        f"{path}{name}.jpg") else "/static/images/no.jpg"

    dp = f"/static/images/{session['username']}.jpg" if os.path.exists(
        f"{path}{session['username']}.jpg") else "/static/images/no.jpg"

    matchs = match(name)

    res = match(session['username'])
    if(res):
        prim = 1 if(len([i[0] for i in res if i[0] == detail[0]])) else 0
        if(prim):
            result = [i for i in res if i[0] == detail[0]][0]

    return render_template(
        "profile.html",
        name=session["username"],
        det=detail,
        img=image,
        pic=dp,
        matches=matchs,
        prime=prim,
        result=result,
        hrf="/logout"
    )


if __name__ == "__main__":
    app.run(debug=True)
