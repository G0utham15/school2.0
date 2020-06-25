from flask import Flask, render_template, jsonify
from users import User

app=Flask(__name__)



@app.route('/')
def home():
    return render_template('home.html')

@app.route('/stu/login')
def stud_login():
    return render_template('student.html')

@app.route('/parent/login')
def parent_login():
    return render_template('parents.html')

@app.route('/staff/login')
def staff_login():
    return render_template('teacher.html')

@app.route('/admin')
def dashboard():
    return render_template("dashboard.html")

if __name__=='__main__':
    app.run(debug=True)