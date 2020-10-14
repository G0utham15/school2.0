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
import logger
import numpy as np
from user import User

client = pymongo.MongoClient(
    "mongodb+srv://g0utham:Sg106271@cluster0-v0h6w.gcp.mongodb.net/?retryWrites=true&w=majority"
)
db = client.school_manage

app = Flask(__name__)
app.config.from_object('config')

def is_human(captcha_response):
    payload = {'response':captcha_response, 'secret':app.config['RECAPTCHA_SECRET_KEY']}
    response = requests.post("https://www.google.com/recaptcha/api/siteverify", payload)
    response_text = json.loads(response.text)
    print(response_text)
    return response_text['success']



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
    if app.config['DEBUG'] == False:
        app.permanent_session_lifetime = timedelta(minutes=15)


@app.route("/",methods=['GET','POST'])
def home():
    try:
        if session["logged_in"]:
            return redirect(url_for("landin"))
    except:
        return render_template("user/login.html", keys=app.config['RECAPTCHA_SITE_KEY'])

@app.route("/#")
def landin():
    announce = list(db.announcements.find({}))
    if session["user"]["role"] == "student":
        cls_mess = list(db.class_messages.find({}))
        return render_template(
            "acad/landin.html", role=session["user"]["role"], ann=announce, cls_msg=cls_mess
        )
    elif session['user']['role']=="admin":
        active_users=list(db.active.find({}))
        user_count=[len([i for i in active_users if i['role']=='admin']), len([i for i in active_users if i['role']=='staff'])\
            , len([i for i in active_users if i['role']=='student'])]
        return render_template("acad/landin.html", role=session["user"]["role"], ann=announce, active_users=active_users, user_count=user_count)
    return render_template("acad/landin.html", role=session["user"]["role"], ann=announce)

##### User Auth and Adding users

@app.route("/attend")
def attend():
    return render_template("acad/attendance.html")

@app.route("/login", methods=["POST"])
def login():
    cred = db.cred.find_one({"username": request.form.get("username").lower()})
    if is_human(request.form['g-recaptcha-response']) and not app.config['DEBUG']:
        if cred and sha256_crypt.verify(request.form.get("password"), cred["password"]):
            return User().start_session(
                db.user_details.find_one({"_id": cred["username"]})
            )
    elif app.config['DEBUG']:
        if cred and sha256_crypt.verify(request.form.get("password"), cred["password"]):
            return User().start_session(
                db.user_details.find_one({"_id": cred["username"]})
            )
    flash("User not Found, Contact School Admin")
    return redirect("/")


@app.route("/adduser", methods=["GET", "POST"])
def adduser():
    return render_template("user/signup.html")


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
        return render_template("acad/results.html",courses=courses)
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
        return render_template("acad/results.html", marks=marks, mark=mark)

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
    return render_template("acad/post_results.html", stud=stud, class_sel=class_sel['class'])

@app.route("/postresults", methods=["POST", "GET"])
def postres():

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
        return render_template("acad/fail.html",res=res, posFail=posFail)

##### Posting class messages and announcements


@app.route("/updates", methods=["POST", "GET"])
def updates():
    return render_template(
        "comm/announce.html", role=session["user"]["role"], id=session["user"]["_id"]
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
        "comm/class_messages.html", course_list=course_list, n=len(course_list)
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
        return render_template("acad/courses.html", courses=courses)
    elif session["user"]["role"] != "admin":
        courses = db.courses.find({"class": "{}".format(session["user"]["class"])})
        return render_template("acad/courses.html", courses=courses)
    return render_template("acad/courses.html")


@app.route("/set_courses", methods=["GET", "POST"])
def set_courses():
    User().courses(request.form)
    return redirect("/courses")


##### Search and view details


@app.route("/user")
def user():
    users = list(db.user_details.find({}).limit(10))
    return render_template("user/user_search.html", users=users)


@app.route("/details", methods=["GET", "POST"])
def get_details():
    print(session["user"])
    return render_template("user/details.html")


@app.route("/fee")
def fee():
    if session["user"]["role"] == "student":
        fee_payable = db.feePerClass.find(
            {"class": "{}".format(session["user"]["class"])}
        )
        fee_payable = list(fee_payable)[0]
        return render_template("acad/fee.html", fee=fee_payable)
    return render_template("acad/fee.html")


@app.route("/set_fee", methods=["GET", "POST"])
def set_fee():
    User().stu_fee(request.form)
    return redirect("/")


#### In Progress


@app.route("/construct")
def construct():
    return render_template("error/construct.html")


@app.route("/setPass")
def setPass():
    return render_template("user/setpass.html")

@app.route("/resSetPass", methods=['GET', 'POST'])
def resSetPass():
    details=request.form
    if not db.cred.find({"_id":details.get("username")}):
        cred = {
                "_id": details.get("username"),
                "username": details.get("username").lower(),
                "password": sha256_crypt.hash(details.get("password")),
            }
        db.cred.insert_one(cred)
        flash("Password is Set. You Can login Now :)")
        return redirect("/")
    flash("User Already exists. Please Login")
    return redirect("/")

@app.route("/updatePass")
def updatePass():
    return render_template("user/updatepass.html")

@app.route("/resUpdatePass", methods=["GET", "POST"])
def resUpdatePass():
    passwd = request.form
    db.cred.update_one({"_id": session["user"]["_id"]}, {"$set": {"password": sha256_crypt.hash(passwd.get("password"))}})
    return redirect("/details")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)