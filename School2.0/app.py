from flask import Flask, render_template, jsonify, session, redirect, request, url_for
import uuid
import pymongo
from passlib.hash import pbkdf2_sha256

client = pymongo.MongoClient("mongodb+srv://g0utham:Sg106271@cluster0-v0h6w.gcp.mongodb.net/?retryWrites=true&w=majority")
db = client.school_manage

secret_key="kqwflslciunWEUYSDFCNCwelsgfkhwwvfli535sjsdivbloh"


class User:
    def start_session(self, user):
        del user['password']
        session['logged_in'] = True
        session['user'] = user
        return jsonify(user), 200

    def signout(self):
        session.clear()
        return redirect('/')
    def add_user(self, details):
        user={
            "_id": uuid.uuid4().hex,
            "name": details.get('name'),
            "username": details.get('username'),
            "password": details.get('password')
        }
        user['password'] = pbkdf2_sha256.encrypt(user['password'])
        if db.users.find_one({ "username": user['username'] }):
                return jsonify({ "error": "ID already in use" }), 400

        if db.users.insert_one(user):
            return self.start_session(user)

        return jsonify({ "error": "Signup failed" }), 400

    def stu_details(self):
        user = {
            "_id": "",
            "Name": "",
            "DOB": "",
            "Gender": "",
            "DOA": "",
            "Class": "",
            "Mobile": "",
            "email": "",
            "password": "",
        }
        return jsonify(user)

    def teacher_details(self):
        user = {
            "_id": "",
            "Name": "",
            "DOB": "",
            "Gender": "",
            "DOA": "",
            "Mobile": "",
            "email": "",
            "emp_id": "",
            "password": "",
        }
        return jsonify(user)

    def teacher_marks(self):
        marks = {
            "_id": "",
            "Reg_no": "",
            "sub_id": "",
            "exam_name": ""
        }

    def login(self):
        user = db.users.find_one({
            "email": request.form.get('email')
        })

        if user and pbkdf2_sha256.verify(request.form.get('password'), user['password']):
            return self.start_session(user)

        return jsonify({"error": "Invalid login credentials"})

app=Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/stu/<id>')
def stud_login(id):
    return render_template('student.html')

@app.route('/parent/<id>')
def parent_login(id):
    return render_template('parents.html')

@app.route('/staff/<id>')
def staff_login(id):
    return render_template('teacher.html')

@app.route('/admin')
def dashboard():
    return render_template("dashboard.html")

@app.route('/login', methods=['POST'])
def login():
    return User().login()

@app.route('/signup', methods=['GET','POST'])
def signup():
    return render_template('signup.html')

@app.route('/result', methods=['GET', 'POST'])
def result():
    cur_user=User()
    result=request.form
    cur_user.add_user(result)
    if result.get('username')[0]=='S' or result.get('username')[0]=='s':
        return redirect('/stu/{}'.format(result.get('username')))
    elif result.get('username')[0]=='P' or result.get('username')[0]=='p':
        return redirect('/parent/{}'.format(result.get('username')))
    elif result.get('username')[0]=='T' or result.get('username')[0]=='t':
        return redirect('/staff/{}'.format(result.get('username')))

if __name__=='__main__':
    app.run(debug=True)