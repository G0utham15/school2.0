from flask import Flask, render_template, jsonify, session, redirect, request, url_for
import uuid
import pymongo
from datetime import datetime
from passlib.hash import sha256_crypt

client = pymongo.MongoClient("mongodb+srv://g0utham:Sg106271@cluster0-v0h6w.gcp.mongodb.net/?retryWrites=true&w=majority")
db = client.school_manage

class User:
    def start_session(self, user):
        del user['password']
        session['start_time']=datetime.now()
        session['logged_in'] = True
        session['user'] = user
        
        return redirect('/#')

    def announce(self, announce, id):
        announcement={
            "_id": uuid.uuid4().hex,
            "title":announce.get('title'),
            "content": announce.get('content'),
            "posted by": id
        }
        if db.announcements.insert_one(announcement):
            return redirect('/')

    def signout(self):
        session['out_time']=datetime.now()
        log={
            'user':session['user'],
            'start_time':session['start_time'],
            'end_time':session['out_time']
        }
        db.user_log.insert_one(log)
        session.clear()
        return redirect('/')
    
    def add_user(self, details):
        user={
            "_id": uuid.uuid4().hex,
            "name": details.get('name'),
            "username": details.get('username'),
            "password": details.get('password'),
            "role":details.get('role'),
            "dob":details.get('dob'),
            "gender":details.get('gender'),
            "doa":details.get('doa'),
            "mobile":details.get('mobile'),
            "email":details.get('email'),
            "class":details.get('class')
        }
        user['password'] = sha256_crypt.hash(user['password'])
        
        if db.users.find_one({ "username": user['username'] }):
            return jsonify({ "error": "ID already in use" }), 400

        if db.users.insert_one(user):
            return self.start_session(user)

        return jsonify({ "error": "Signup failed" }), 400

    def stu_fee(self, fee):
        user = {
            "_id": uuid.uuid4().hex,
            "class": fee.get("class"),
            "fee":fee.get('fee'),
        }
        if db.feePerClass.find_one({ "class":user['class']}):
            db.feePerClass.update_one(user)
        if db.feePerClass.insert_one(user):
            return redirect('/fee')
        return redirect('/')

    def teacher_update(self):
        user = {
            "_id": "",
            "Name": "",
            "DOB": "",
            "Gender": "",
            "DOA": "",
            "Mobile": "",
            "email": "",
            "emp_id": "",
            "salary":""
        }
        return jsonify(user)

    def marks(self):
        marks = {
            "_id": uuid.uuid4().hex,
            "class_id":"",
            "exam_name": "",
            "sub_id": "",
            "Reg_no": "",
        }
    
    def courses(self, course):
        course={
            "_id":uuid.uuid4().hex,
            "course_id":course.get('course_id'),
            "class_id":course.get('class_id'),
            "course_name":course.get('course_name'),
            "class":course.get('class'),
            "faculty_id":course.get('faculty_id'),
        }
        course['students_enrolled']=[i["username"] for i in list(db.users.find({"class":"{}".format(course["class"])}))]
        db.courses.insert_one(course)
        return redirect('/courses')

    def login(self):
        user = db.users.find_one({
            "username": request.form.get('username')
        })

        if user and sha256_crypt.verify(request.form.get('password'), user['password']):
            return self.start_session(user)

        return redirect('/')
        

app=Flask(__name__)

@app.route('/')
def home():
    try:
        if session['logged_in']:
            return redirect(url_for('landin'))
    except:
        return render_template('login.html')
@app.route('/#')
def landin():
    announce=list(db.announcements.find({}))
    return render_template('landin.html', role= session['user']['role'], ann=announce)

@app.route('/login', methods=['POST'])
def login():
    return User().login()

@app.route('/adduser', methods=['GET','POST'])
def adm_signup():
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session['logged_in']=False
    return User().signout()

@app.route('/result', methods=['GET', 'POST'])
def result():
    result=request.form

    User().add_user(result)
    print('user added')
    if result['role']=='admin':
        return redirect('/adduser')
    else:
        return redirect('/#')

@app.route('/marks')
def marks():
    pass

@app.route('/post/', methods=['POST','GET'])
def announce():
    ann=request.form
    print(ann)
    User().announce(ann, session['user']['username'])
    return redirect('/')

@app.route('/courses')
def add_courses():
    if session['user']['role']=='staff':
        courses=db.courses.find({'faculty_id':"{}".format(session['user']['username'])})
        return render_template('courses.html', courses=courses)
    elif session['user']['role']!='admin':
        courses=db.courses.find({'class':"{}".format(session['user']['class'])})
        return render_template('courses.html', courses=courses)
    return render_template('courses.html')
@app.route('/set_courses', methods=['GET', "POST"])
def set_courses():
    User().courses(request.form)
    return redirect('/courses')

@app.route('/updates/', methods=['POST', 'GET'])
def announcements():
    return render_template('announce.html', role=session['user']['role'], id=session['user']['username'])

@app.route('/details/', methods=['GET', 'POST'])
def get_details():
    return jsonify(session['user'])

@app.route('/fee_pay')
def get_fee():
    if session['user']['role']=="student":
        fee_payable=db.feePerClass.find({'class':"{}".format(session['user']['class'])})
        fee_payable=list(fee_payable)[0]
        return render_template('fee.html', fee=fee_payable)
    return render_template('fee.html')

@app.route('/set_fee', methods=['GET', 'POST'])
def set_fee():
    User().stu_fee(request.form)
    return redirect('/')

if __name__=='__main__':
    app.secret_key="kqwflslciunWEUYSDFCNCwelsgfkhwwvfli535sjsdivbloh"
    app.run(debug=False)