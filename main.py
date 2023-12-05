import json
import hashlib
import jwt

from flask import Flask, request, jsonify
from flask_mysqldb import MySQL
import sqlalchemy.exc
from enum import Enum
from functools import wraps


app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'inse6421'

mysql = MySQL(app)

def token_required(role: [Enum] = []):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            print(role)
            token = None
            if "Authorization" in request.headers:
                token = request.headers["Authorization"].split(" ")[1]
            if not token:
                return {
                    "message": "Authentication Token is missing!",
                    "data": None,
                    "error": "Unauthorized"
                }, 401
            try:
                data=jwt.decode(token, "samdfbnb324m13nb41k3b41mn3bn4bnm13bmn4b3k4bk134nb1m,4b", algorithms=["HS256"])

                cursor = mysql.connection.cursor()
                cursor.execute("SELECT student_id, role FROM user WHERE student_id=" + data['student_id'])
                current_user = cursor.fetchone()
                print(current_user)
                if current_user is None:
                    return {
                    "message": "Invalid Authentication token!",
                    "data": None,
                    "error": "Unauthorized"
                }, 401

                if current_user[1] not in role:
                    return {
                        "message": "UPPS!YOU DO NOT HAVE ACCESS",
                        "data": None,
                        "error": "Forbidden"
                    }, 403

            except Exception as e:
                return {
                    "message": "Something went wrong",
                    "data": None,
                    "error": str(e)
                }, 500

            return f()
        return decorated
    return decorator

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/login", methods = ['POST'])
def login():
    student_id = request.json['student_id']
    password = hashlib.md5(request.json['password'].encode()).hexdigest()

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, student_id FROM user WHERE student_id=%s AND password=%s", (student_id, password))
    user = cursor.fetchone()
    cursor.close();
    if user:
        encoded_jwt = jwt.encode({"student_id" : user[1]}, "samdfbnb324m13nb41k3b41mn3bn4bnm13bmn4b3k4bk134nb1m,4b", algorithm="HS256")
        return jsonify({"_token": encoded_jwt})
    else:
        return jsonify("Invalid Credentials!")

@app.route("/registration", methods = ['POST'])
def registration():
    student_id = request.json['student_id']
    password = request.json['password']
    # print(student_id)
    if len(password) > 8:

        password = hashlib.md5(request.json['password'].encode()).hexdigest()
        fullname = request.json['full_name']
        email = request.json['email']
        role = request.json['role']
    else:
        return jsonify({"message": "Please try a password more that 8 character"})
    response = {}

    try:
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO user(student_id, password, full_name, email, role) VALUES(%s, %s, %s, %s, %s)", (student_id, password, fullname, email, role))
        mysql.connection.commit()
        response = {"response": "User Inserted Successfully!"}
    except Exception as e:
        response = {"response": format(e)}

    return jsonify({"message": response})

@app.route("/getallusers", methods = ['GET'])
@token_required(role=["admin"])
def getAllUsers():
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM user")
    data = cursor.fetchall()
    cursor.close()
    return jsonify(data)

@app.route("/getprofile", methods = ['GET'])
@token_required(role=["admin", "student"])
def getprofile():
    student_id = request.args.get('student_id')
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM user where student_id ="+student_id)
    data = cursor.fetchall()
    cursor.close()
    return jsonify(data)

@app.route("/deleteuser", methods = ['DELETE'])
@token_required(role=["admin"])
def deleteuser():
    student_id = request.json['student_id']
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("DELETE FROM user where student_id ="+student_id)
        check = cursor.rowcount
        cursor.close()
        print(mysql.connection.commit())
        if check == 0:
            response = "No user found"
        else:
            response = "User deleted"
    except Exception as e:
        response = format(e)

    return jsonify({"message": response})
