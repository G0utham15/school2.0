from flask import jsonify
class User:
    def stu_signup(self):
        user={
            "_id":"",
            "Name":"",
            "DOB" : "",
            "Gender" : "",
            "DOA" : "",
            "Class" : "",
            "Mobile":"",
            "email":"",
            "password":"",
        }
        return jsonify(user)
    
    def teacher_signup(self):
        user={
            "_id":"",
            "Name":"",
            "DOB" : "",
            "Gender" : "",
            "DOA":"",
            "Mobile":"",
            "email":"",
            "emp_id":"",
            "password":"",
        }
        return jsonify(user)