from flask import (
    Flask,
    render_template,
    jsonify,
    session,
    redirect,
    request,
    url_for,
    flash,
)
import uuid
import pymongo
from datetime import datetime, timedelta
from passlib.hash import sha256_crypt
import os
import requests
import json
client = pymongo.MongoClient(
    "mongodb+srv://g0utham:Sg106271@cluster0-v0h6w.gcp.mongodb.net/?retryWrites=true&w=majority"
)
db = client.school_manage


class User:
    def start_session(self, user):
        session["logged_in"] = True
        session["user"] = user
        db.active.insert_one(user)
        return redirect("/#")

    def announce(self, announce, id):
        announcement = {
            "_id": uuid.uuid4().hex,
            "title": announce.get("title"),
            "content": announce.get("content"),
            "Priority": announce.get("priority"),
            "class_id": announce.get("class"),
            "posted by": id,
        }
        if db.announcements.insert_one(announcement):
            return redirect("/")

    def signout(self):
        db.active.delete_one({"_id":session['user']['_id']})
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

    def courses(self, course):
        course = {
            "_id": uuid.uuid4().hex,
            "course_id": course.get("course_id"),
            "class": course.get("class"),
            "course_name": course.get("course_name"),
            "faculty_id": course.get("faculty_id"),
        }
        course["students_enrolled"] = [
            i["_id"] for i in list(db[course["class"]].find({}))
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
        cred = {
            "_id": details.get("username"),
            "username": details.get("username").lower(),
            "password": sha256_crypt.hash(details.get("password")),
        }
        user_det = {"_id": user["_id"], "name": user["name"], "class_id": user["class"]}
        try:
            if db.cred.find_one({"username": user["username"]}):
                return jsonify({"error": "ID already in use"}), 400
        except:
            if db.cred.insert_one(cred):
                db.user_details.insert_one(user)
                if user["role"] == "student":
                    db[user["class"]].insert_one(user_det)
                return redirect("/adduser")
        return jsonify({"error": "Signup failed"}), 400

    def login(self):
        cred = db.cred.find_one({"username": request.form.get("username").lower()})
        if is_human(request.form['g-recaptcha-response']) and debug==False:
            if cred and sha256_crypt.verify(request.form.get("password"), cred["password"]):
                return self.start_session(
                    db.user_details.find_one({"_id": cred["username"]})
                )
        elif debug==True:
            if cred and sha256_crypt.verify(request.form.get("password"), cred["password"]):
                return self.start_session(
                    db.user_details.find_one({"_id": cred["username"]})
                )
        flash("User not Found, Contact School Admin")
        return redirect("/")

def is_human(captcha_response):
    secret = "6LdMW9EZAAAAABzv_SguBzMlqgdOOkDPnJcKRbzb" 
    payload = {'response':captcha_response, 'secret':secret}
    response = requests.post("https://www.google.com/recaptcha/api/siteverify", payload)
    response_text = json.loads(response.text)
    print(response_text)
    return response_text['success']

app = Flask(__name__)


@app.errorhandler(500)
def server_error(e):
    try:
        db.active.delete_one({"_id":session['user']['_id']})
    except:
        pass
    flash("Something went wrong please try again")
    return redirect("/")


@app.before_request
def before_request():
    session.permanent = True
    if debug == False:
        app.permanent_session_lifetime = timedelta(minutes=15)


@app.route("/",methods=['GET','POST'])
def home():
    try:
        if session["logged_in"]:
            return redirect(url_for("landin"))
    except:
        return render_template("login.html", keys=captcha_keys[0])


@app.route("/#")
def landin():
    announce = list(db.announcements.find({}))
    if session["user"]["role"] == "student":
        cls_mess = list(db.class_messages.find({}))
        return render_template(
            "landin.html", role=session["user"]["role"], ann=announce, cls_msg=cls_mess
        )
    elif session['user']['role']=="admin":
        active_users=list(db.active.find({}))
        user_count=[len([i for i in active_users if i['role']=='admin']), len([i for i in active_users if i['role']=='staff'])\
            , len([i for i in active_users if i['role']=='student'])]
        return render_template("landin.html", role=session["user"]["role"], ann=announce, active_users=active_users, user_count=user_count)
    return render_template("landin.html", role=session["user"]["role"], ann=announce)


##### User Auth and Adding users

@app.route("/attend")
def attend():
    return render_template("attendance.html")

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


@app.route("/adduserRes", methods=["GET", "POST"])
def result():
    result = request.form
    User().add_user(result)
    if result["role"] == "admin":
        return redirect("/adduser")
    else:
        return redirect("/#")


##### Posting results
@app.route("/results")
def results():
    if session["user"]["role"] == "staff":
        courses = list(db.courses.find({"faculty_id": session["user"]["_id"]}))
        return render_template("results.html",courses=courses)
    elif session['user']['role']=="student":
        marks = list(db.results.find({"class": session["user"]["class"]}))
        courses=list(set([i['course_id'] for i in marks]))
        mark={}
        for i in sorted(courses):
            mark[i]={}
            mark[i]['total']=0
            mark[i]['totMax']=0
            mark[i]['mean']=0
            mark[i]['stDev']=0
            mark[i]['maxMarks']={}
            mark[i]['clsAvg']=[]
            for j in marks:
                if j['course_id']==i:
                    mark[i][j['exam']]=j['marks'][session['user']['_id']]
                    mark[i]['total']+=j['marks'][session['user']['_id']]
                    mark[i]['totMax']+=j['maxMarks']
                    mark[i]['mean']+=j['mean']
                    mark[i]['stDev']+=j['std']**2
                    mark[i]['maxMarks'][j['exam']]=j['maxMarks']
                    mark[i]['clsAvg'].append(j['mean'])
            mark[i]['stDev']=round(mark[i]['stDev']**0.5, 2)
            mark[i]['predGrad'], mark[i]['color']=grade(mark[i]['total'], mark[i]['mean'], mark[i]['stDev'], mark[i]['totMax'])
        print(mark)
        return render_template("results.html", marks=marks, mark=mark)

def grade(scored, mean, stDev, total):
    if scored>=mean+1.5*stDev:
        if scored>0.9*total:
            return 'S', 'success'
        else:
            return 'A', 'success'
    elif scored>=mean+0.5*stDev and scored<mean+1.5*stDev:
        return 'A', 'success'
    elif scored>=mean-0.5*stDev and scored<mean+0.5*stDev:
        return 'B', 'secondary'
    elif scored>=mean-1*stDev and scored<mean-0.5*stDev:
        return 'C', 'warning'
    elif scored>=mean-1.5*stDev and scored<mean-1*stDev:
        return 'D', 'warning'
    elif scored>=mean-2*stDev and scored<mean-1.5*stDev:
        return 'E', 'danger'    
    elif scored<mean-2*stDev or scored<0.4*total:
        return 'F', 'danger'

@app.route("/marks", methods=['GET', 'POST'])
def marks():
    class_sel=request.form
    stud = list(db[class_sel['class']].find({}))
    return render_template("post_results.html", stud=stud, class_sel=class_sel['class'])

@app.route("/postresults", methods=["POST", "GET"])
def postres():
    import numpy as np
    res = request.form
    course_name=list(db.courses.find({"class":res.get("class"), "faculty_id":session['user']['_id']}))[0]['course_name']
    course_id=list(db.courses.find({"class":res.get("class"), "faculty_id":session['user']['_id']}))[0]['course_id']
    students=list(res.keys())[3:]
    avg=np.average([int(res.get(i)) for i in students])
    stDev=np.std([int(res.get(i)) for i in students])
    mark={i: int(res.get(i)) for i in students}
    marks = {
        "_id": uuid.uuid4().hex,
        "course_id":course_id,
        "course_name":course_name,
        "user": session["user"]["name"],
        "class": res.get('class'),
        "exam": res.get('exam'),
        "maxMarks": int(res.get('maxMarks')),
        "marks":mark,
        "mean":round(avg, 2),
        "std":round(stDev, 2),
    }
    db.results.insert_one(marks)
    return redirect("/results")

def possFail(res):
    marks = list(db.results.find({"user": session["user"]["_id"]}))
    courses = list(db.courses.find({"faculty_id": session["user"]["_id"]}))
    course={i['course_id']:i['students_enrolled'] for i in courses}
    top={}
    avg={}
    fail={}
    tot={}
    predGrade={}
    for i in course:
        top[i]=[]
        avg[i]=[]
        fail[i]=[]
        tot[i]={}
        tot[i]['maxMarks']=0
        tot[i]['mean']=0
        tot[i]['stDev']=0
        for j in marks:
            if i==j['course_id']:
                tot[i]['maxMarks']+=j['maxMarks']
                tot[i]['mean']+=j['mean']
                tot[i]['stDev']+=j['std']**2

                for k in course[i]:
                    try:
                        tot[i][k]+=j['marks'][k]
                    except:
                        tot[i][k]=0
                        tot[i][k]+=j['marks'][k]
        tot[i]['stDev']=round(tot[i]['stDev']**0.5,2)
        for j in course[i]:
            if grade(tot[i][j],tot[i]['mean'], tot[i]['stDev'], tot[i]['maxMarks'])[0] in ['A', 'S']:
                top[i].append(j)
            elif grade(tot[i][j],tot[i]['mean'], tot[i]['stDev'], tot[i]['maxMarks'])[0] in ['B', 'C', 'D']:
                avg[i].append(j)
            else:
                fail[i].append(j)
        predGrade[i]={'top':top[i], 'avg':avg[i], 'fail':fail[i]}
        
    return predGrade


@app.route("/fail")
def fail():
    if session["user"]["role"] == "staff":
        res=list(db.results.find({"user":session['user']["name"]}))
        posFail=possFail(res)
        return render_template("fail.html",res=res, posFail=posFail)

##### Posting class messages and announcements


@app.route("/updates", methods=["POST", "GET"])
def updates():
    return render_template(
        "announce.html", role=session["user"]["role"], id=session["user"]["_id"]
    )


@app.route("/post", methods=["POST", "GET"])
def announce():
    ann = request.form
    User().announce(ann, session["user"]["_id"])
    return redirect("/")


@app.route("/classmsg", methods=["GET", "POST"])
def classmsg():
    courses = db.courses.find({"faculty_id": "{}".format(session["user"]["_id"])})
    course_list = [i["course_name"] for i in courses]
    return render_template(
        "class_messages.html", course_list=course_list, n=len(course_list)
    )


@app.route("/postclsmsg", methods=["GET", "POST"])
def postclsmsg():
    message = request.form
    course_name=list(db.courses.find({"class":message.get("class"), "faculty_id":session['user']['_id']}))[0]['course_name']
    course_id=list(db.courses.find({"class":message.get("class"), "faculty_id":session['user']['_id']}))[0]['course_id']
    new_message = {
        "_id": uuid.uuid4().hex,
        "course_id":course_id,
        "course_name":course_name,
        "message": message.get("content"),
        "title":message.get('title'),
        "priority": message.get("priority"),
        "class":message.get("class"),
        "from":session['user']['name']
    }
    db.class_messages.insert_one(new_message)
    return redirect("/")


##### Assign Courses


@app.route("/courses")
def add_courses():
    if session["user"]["role"] == "staff":
        courses = db.courses.find({"faculty_id": "{}".format(session["user"]["_id"])})
        return render_template("courses.html", courses=courses)
    elif session["user"]["role"] != "admin":
        courses = db.courses.find({"class": "{}".format(session["user"]["class"])})
        return render_template("courses.html", courses=courses)
    return render_template("courses.html")


@app.route("/set_courses", methods=["GET", "POST"])
def set_courses():
    User().courses(request.form)
    return redirect("/courses")


##### Search and view details


@app.route("/user")
def user():
    users = list(db.user_details.find({}).limit(10))
    return render_template("user_search.html", users=users)


@app.route("/details", methods=["GET", "POST"])
def get_details():
    print(session["user"])
    return render_template("details.html")


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


#### In Progress


@app.route("/construct")
def construct():
    return render_template("construct.html")


@app.route("/setpass")
def setpass():
    return render_template("setpass.html")


@app.route("/updatepass")
def updatepass():
    return render_template("updatepass.html")


@app.route("/resupdatepass", methods=["GET", "POST"])
def resupdatepass():
    passwd = request.form
    old_passwd = db.cred.find({"username": session["user"]["_id"]})
    db.cred.update_one({{"username": session["user"]["_id"]}, {"$set": update}})
    return redirect("/updatepass")


if __name__ == "__main__":
    app.secret_key = "kqwflslciunWEUYSDFCNCwelsgfkhwwvfli535sjsdivbloh"
    port = int(os.environ.get("PORT", 5000))
    captcha_keys=["6LdMW9EZAAAAABNTDJZnqKLunWo3G_j1t7hr8Zal"]
    debug = False
    host = "127.0.0.1" if debug else "0.0.0.0"
    app.run(host=host, port=port, debug=debug)