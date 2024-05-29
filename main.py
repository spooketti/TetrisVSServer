from flask import Flask, request, jsonify, make_response, Response
from threading import Thread
from init import app, socketio
from flask_sqlalchemy import SQLAlchemy 
from flask_socketio import join_room
from sqlalchemy import and_
from authToken import token_required
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from init import db, cors
import time
from model.user import Users, initUserTable
from model.leaderboard import Leaderboard, initLeaderboard, Scores, initScores
import datetime
import json


@app.route('/')
def home():
    return "TetrisVS's Server"

@app.before_request
def before_request():
    allowed_origin = request.headers.get('Origin')
    if allowed_origin in ['http://localhost:4100', 'http://172.27.233.236:8080','https://spooketti.github.io']:
        cors._origins = allowed_origin
        
@app.route("/signup/", methods=["POST"])
def signup():
    data = request.get_json()
    hashed_password = generate_password_hash(data['password'], method='pbkdf2:sha256')
    user = Users(userID = data["userID"], password=hashed_password, username=data["username"],pfp=data["pfp"]) 
    try:
        db.session.add(user)  
        db.session.commit()
    except:
        return jsonify({"error":"UserID taken!"})
    token = jwt.encode({'userID' : user.userID, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=60)}, app.config['SECRET_KEY'], algorithm="HS256")
    response = {"jwt":token}
    json_data = json.dumps(response)
    resp = Response(json_data, content_type="application/json")
    resp.set_cookie("jwt", token,
                                max_age=3600,
                                secure=True,
                                httponly=True,
                                path='/',
                                samesite='None',  # cite
                                domain="172.27.233.236"
                                )
    return resp

@app.route('/auth/', methods=['GET']) #check if the user exists
@token_required
def auth(current_user):
    
    return jsonify({'pfp': current_user.pfp,
                    "username":current_user.username,
                    "userID":current_user.userID,
                    "joindate":current_user.date,
                    "bio":current_user.bio
                    })


def partition(arr, low, high):
    pivot = arr[high]["highScore"]
    index1 = low - 1

    for index2 in range(low, high):
        if arr[index2]["highScore"] <= pivot:
            index1 += 1
            temp = arr[index1]
            arr[index1] = arr[index2]
            arr[index2] = temp
    
    temp = arr[high]
    arr[high] = arr[index1 + 1]
    arr[index1 + 1] = arr[high]
    return index1 + 1


def quicksort(arr, low, high):
    if low < high:
        pivot_index = partition(arr, low, high)
        quicksort(arr, low, pivot_index-1)
        quicksort(arr, pivot_index+1, high)



@app.route('/getLeaderboard/', methods=['GET'])
def getLeaderboard():
    leaderboard = Leaderboard.query.all()
    arr = [entry.read() for entry in leaderboard]
    quicksort(arr, 0, len(arr) - 1)
    return jsonify(arr)




@app.route('/login/', methods=['POST'])  
def login_user(): 
    data = request.get_json()
    loginID = data["userID"]
    loginPW = data["password"]
    user = Users.query.filter_by(userID=loginID).first()
    if not user:
        response = {"error":"User does not exist!"}
        return jsonify(response)
    
    if check_password_hash(user.password, loginPW):
        token = jwt.encode({'userID' : user.userID, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=60)}, app.config['SECRET_KEY'], algorithm="HS256")
        response = {"jwt":token}
        json_data = json.dumps(response)
        resp = Response(json_data, content_type="application/json")
        
        resp.set_cookie("jwt", token,
                                max_age=3600,
                                secure=True,
                                httponly=True,
                                path='/',
                                samesite='None',  # cite
                                domain="172.27.233.236"
                                )
        return resp


    return make_response('Invalid Credentials',  401, {'Authentication': '"login required"'})

@app.route("/updateUser/",methods=["POST"])
@token_required
def updateUser(current_user):
    data = request.get_json()
    user = Users.query.filter_by(userID=current_user.userID).first()
    return user.update(data["oldPW"],data["newPW"],data["username"],data["pfp"],data["bio"])

@app.route("/saveScore/", methods=["POST"])
@token_required
def updateScore(current_user):
    data = request.get_json()
    try:
        score = data['score']
        print(type(score))
        score = int(score)
    except:
        return "Score is not a valid integer"
    date = datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    newScore = Scores(user=current_user.userID, score=score, date=date)
    db.session.add(newScore)
    user = Leaderboard.query.filter_by(user=current_user.userID)
    user.update(score, date)
    highScore = True
    db.session.commit()
    if highScore:
        return f"Score saved successfully. New high score of {score}!"
    else:
        return "Score saved successfully. No new high score."


def run():
    app.run(host='0.0.0.0',port=8086)

initUserTable()
initLeaderboard()
initScores()
run()