from flask import Flask, render_template, jsonify, session, redirect, request, url_for, flash
import uuid
import pymongo
from datetime import datetime, timedelta
from passlib.hash import sha256_crypt
import os

client = pymongo.MongoClient(
    "mongodb+srv://g0utham:Sg106271@cluster0-v0h6w.gcp.mongodb.net/?retryWrites=true&w=majority"
)
db = client.school_manage


class User:
    def start_session(self, user):
        session["logged_in"] = True
        session["user"] = user
        print("Session Started")
        return redirect("/#")

    def announce(self, announce, id):
        announcement = {
            "_id": uuid.uuid4().hex,
            "title": announce.get("title"),
            "content": announce.get("content"),
            "Priority":announce.get("priority"),
            "posted by": id,
        }
        if db.announcements.insert_one(announcement):
            return redirect("/")

    def signout(self):
        session.clear()
        flash("You have logged out successfully")
        return redirect("/")


    def stu_fee(self, fee):
        user = {
            "_id": uuid.uuid4().hex,
            "class": fee.get("class"),
            "fee": fee.get("fee"),
        }
        if db.feePerClass.find_one({"class": user["class"]}):
            db.feePerClass.update_one(user)
        if db.feePerClass.insert_one(user):
            return redirect("/fee")
        return redirect("/")

    def marks(self):
        marks = {
            "_id": uuid.uuid4().hex,
            "class_id": "",
            "exam_name": "",
            "sub_id": "",
        }

    def courses(self, course):
        course = {
            "_id": uuid.uuid4().hex,
            "course_id": course.get("course_id"),
            "class_id": course.get("class_id"),
            "course_name": course.get("course_name"),
            "class": course.get("class"),
            "faculty_id": course.get("faculty_id"),
        }
        course["students_enrolled"] = [
            i["username"]
            for i in list(db.users.find({"class": "{}".format(course["class"])}))
        ]
        db.courses.insert_one(course)
        return redirect("/courses")

    def add_user(self, details):
        user = {
            "_id": details.get("username"),
            "name": details.get("name"),
            "role": details.get("role"),
            "dob": details.get("dob"),
            "gender": details.get("gender"),
            "doa": details.get("doa"),
            "mobile": details.get("mobile"),
            "email": details.get("email"),
            "class": details.get("class"),
        }
        cred={
            "_id": details.get("username"),
            "username": details.get("username").lower(),
            "password": sha256_crypt.hash(details.get("password")),
        }
        try:
            if db.cred.find_one({"username": user["username"]}):
                return jsonify({"error": "ID already in use"}), 400
        except:
            if db.cred.insert_one(cred):
                db.user_details.insert_one(user)
                if user['role']=='student':
                    db[user['class']].insert_one(user)
                return redirect("/")

        return jsonify({"error": "Signup failed"}), 400


    def login(self):
        cred = db.cred.find_one({"username": request.form.get("username").lower()})
        if cred and sha256_crypt.verify(request.form.get("password"), cred["password"]):
            return self.start_session(db.user_details.find_one({"_id": cred['username']}))
        flash("User not Found, Contact School Admin")
        return redirect("/")


app = Flask(__name__)


@app.errorhandler(500)
def server_error(e):
    flash("Something went wrong please try again", 'error')
    return redirect("/")


@app.before_request
def before_request():
    session.permanent = True
    if debug==False:
        app.permanent_session_lifetime = timedelta(minutes=5)


@app.route("/")
def home():
    try:
        if session["logged_in"]:
            return redirect(url_for("landin"))
    except:
        return render_template("login.html")


@app.route("/#")
def landin():
    announce = list(db.announcements.find({}))
    print("page Landed")
    if session["user"]["role"]=='student':
        cls_mess=list(db.class_messages.find({}))
        return render_template("landin.html", role=session["user"]["role"], ann=announce, cls_msg=cls_mess)
    return render_template("landin.html", role=session["user"]["role"], ann=announce)


@app.route("/login", methods=["POST"])
def login():
    return User().login()


@app.route("/adduser", methods=["GET", "POST"])
def adduser():
    return render_template("signup.html")


@app.route("/logout")
def logout():
    session["logged_in"] = False
    return User().signout()


@app.route("/result", methods=["GET", "POST"])
def result():
    result = request.form
    User().add_user(result)
    if result["role"] == "admin":
        return redirect("/adduser")
    else:
        return redirect("/#")


@app.route("/marks")
def marks():
    pass


@app.route("/post", methods=["POST", "GET"])
def announce():
    ann = request.form
    print(ann)
    User().announce(ann, session["user"]["_id"])
    return redirect("/")


# Courses assigned
@app.route("/courses")
def add_courses():
    if session["user"]["role"] == "staff":
        courses = db.courses.find(
            {"faculty_id": "{}".format(session["user"]["_id"])}
        )
        return render_template("courses.html", courses=courses)
    elif session["user"]["role"] != "admin":
        courses = db.courses.find({"class": "{}".format(session["user"]["class"])})
        return render_template("courses.html", courses=courses)
    return render_template("courses.html")


@app.route("/set_courses", methods=["GET", "POST"])
def set_courses():
    User().courses(request.form)
    return redirect("/courses")


@app.route("/updates", methods=["POST", "GET"])
def updates():
    return render_template(
        "announce.html", role=session["user"]["role"], id=session["user"]["_id"]
    )


@app.route("/details", methods=["GET", "POST"])
def get_details():
    print(session['user'])
    return render_template('details.html')


@app.route("/fee")
def fee():
    if session["user"]["role"] == "student":
        fee_payable = db.feePerClass.find(
            {"class": "{}".format(session["user"]["class"])}
        )
        fee_payable = list(fee_payable)[0]
        return render_template("fee.html", fee=fee_payable)
    return render_template("fee.html")


@app.route("/set_fee", methods=["GET", "POST"])
def set_fee():
    User().stu_fee(request.form)
    return redirect("/")


@app.route("/classmsg", methods=["GET", "POST"])
def classmsg():
    courses = db.courses.find({"faculty_id": "{}".format(session["user"]["username"])})
    course_list = [i["course_name"] for i in courses]
    return render_template(
        "class_messages.html", course_list=course_list, n=len(course_list)
    )


@app.route("/postclsmsg", methods=["GET", "POST"])
def postclsmsg():
    message = request.form
    new_message = {
        "_id": uuid.uuid4().hex,
        "course_name": message.get("course_name"),
        "content": message.get("content"),
        "priority": message.get("priority"),
    }
    db.class_messages.insert_one(new_message)
    return redirect("/classmsg")


@app.route("/construct")
def construct():
    return render_template("construct.html")


if __name__ == "__main__":
    app.secret_key = "kqwflslciunWEUYSDFCNCwelsgfkhwwvfli535sjsdivbloh"
    port = int(os.environ.get("PORT", 5000))
    debug=False
    host="127.0.0.1" if debug else "0.0.0.0"
    app.run(host=host, port=port, debug=debug)