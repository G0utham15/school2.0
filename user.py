import pymongo
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
import smtplib
import uuid
from passlib.hash import sha256_crypt

client = pymongo.MongoClient(
    "mongodb+srv://g0utham:Sg106271@cluster0-v0h6w.gcp.mongodb.net/?retryWrites=true&w=majority"
)
db = client.school_manage

class User:
    def start_session(self, user):
        session["logged_in"] = True
        session["user"] = user
        try:
            db.active.insert_one(user)
        except:
            pass
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
        s = smtplib.SMTP('smtp.gmail.com', 587) 
  
        # start TLS for security 
        s.starttls() 
  
        # Authentication 
        s.login("dev.g0utham15@gmail.com", "Sg106271.5") 
  
        # message to be sent 
        message = "Dear {},\nYour Username assigned is {}.Please set a new password".format(details.get('name'), details.get('username'))
  
        # sending the mail 
        s.sendmail("dev.g0utham15@gmail.com", details.get('email'), message) 
  
        # terminating the session 
        s.quit() 
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
        user_det = {"_id": user["_id"], "name": user["name"], "class_id": user["class"]}
        try:
            if db.cred.find_one({"username": user["username"]}):
                return jsonify({"error": "ID already in use"}), 400
        except:
            if user["role"] == "student":
                db[user["class"]].insert_one(user_det)
            return redirect("/adduser")
        db.user.insert_one(user)
        return jsonify({"error": "Signup failed"}), 400