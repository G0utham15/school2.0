from flask import Flask, render_template, jsonify, session, redirect, request, url_for
import uuid
import pymongo
from passlib.hash import pbkdf2_sha256

client = pymongo.MongoClient("mongodb+srv://g0utham:Sg106271@cluster0-v0h6w.gcp.mongodb.net/?retryWrites=true&w=majority")
db = client.school_manage

class User:
    def start_session(self, user):
        del user['password']
        session['logged_in'] = True
        session['user'] = user
        return redirect('/{}/{}'.format(user.get('role').lower(), user.get('username').lower()))

    def signout(self):
        session.clear()
        return redirect('/')
    
    def add_user(self, details):
        user={
            "_id": uuid.uuid4().hex,
            "name": details.get('name'),
            "username": details.get('username'),
            "password": details.get('password'),
            "role":details.get('role'),
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
            "Mobile": "",
            "email": "",
            "Class": "",
            "stu_id":"",
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
            "username": request.form.get('username')
        })

        if user and pbkdf2_sha256.verify(request.form.get('password'), user['password']):
            return self.start_session(user)

        return jsonify({"error": "Invalid login credentials"})

app=Flask(__name__)

@app.route('/')
def home():
    return render_template('login.html')

@app.route('/<role>/<id>')
def landin(role, id):
    return render_template('landin.html', role= role, id=id)

@app.route('/login', methods=['POST'])
def login():
    return User().login()

@app.route('/adduser', methods=['GET','POST'])
def signup():
    return render_template('signup.html')

@app.route('/logout')
def logout():
    return User().signout()

@app.route('/result', methods=['GET', 'POST'])
def result():
    cur_user=User()
    result=request.form
    cur_user.add_user(result)
    return redirect('/{}/{}'.format(result.get('role').lower(), result.get('username').lower()))
    
@app.route('/details/<id>', methods=['GET', 'POST'])
def details(id):
    return render_template('details.html', id=id)

if __name__=='__main__':
    app.secret_key="kqwflslciunWEUYSDFCNCwelsgfkhwwvfli535sjsdivbloh"
    app.run(debug=True)