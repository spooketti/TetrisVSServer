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

def mergesort(arr):
    if len(arr) <= 1:
        return arr
    mid = len(arr) // 2
    left = mergesort(arr[:mid])
    right = mergesort(arr[mid:])
    return merge(left, right)

def merge(left, right):
    result = []
    while left and right:
        if left[0]["highScore"] > right[0]['highScore']:  # Compare based on the score
            result.append(left.pop(0))
        else:
            result.append(right.pop(0))
    result.extend(left or right)
    return result


@app.route('/getLeaderboard/', methods=['GET'])
def getLeaderboard():
    leaderboard = Leaderboard.query.all()
    lst = [entry.read() for entry in leaderboard]
    sorted_lst = mergesort(lst)
    return jsonify(sorted_lst)




@app.route('/login/', methods=['POST'])  
def login_user(): 
    try:
        body = request.get_json()
        if not body:
            return {
                "message": "Please provide user details",
                "data": None,
                "error": "Bad request"
            }, 400
        ''' Get Data '''
        userID = body.get('userID')
        if userID is None:
            return {'message': f'User ID is missing'}, 400
        password = body.get('password')
        
        ''' Find user '''
        user = Users.query.filter_by(userID=userID).first()
        if user is None or not user.is_password(password):
            return {'message': f"Invalid user id or password"}, 401
        if user:
            try:
                token = jwt.encode(
                    {"userID": user.userID},
                    app.config["SECRET_KEY"],
                    algorithm="HS256"
                )
                resp = Response("Authentication for %s successful" % (user.userID))
                resp.set_cookie("jwt", token,
                        max_age=3600,
                        secure=True,
                        httponly=True,
                        path='/',
                        samesite='None'  # This is the key part for cross-site request
                        # domain="frontend.com"
                        )
                return resp
            except Exception as e:
                return {
                    "error": "Something went wrong",
                    "message": str(e)
                }, 500
        return {
            "message": "Error fetching auth token!",
            "data": None,
            "error": "Unauthorized"
        }, 404
    except Exception as e:
        return {
                "message": "Something went wrong!",
                "error": str(e),
                "data": None
        }, 500
    

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
    userID = current_user.userID
    try:
        score = data['score']
        score = int(score)
    except:
        return "Score is not a valid integer"
    date = datetime.datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    newScore = Scores(user=userID, score=score, date=date)
    db.session.add(newScore)
    curr_user = Leaderboard.query.filter_by(user=userID).first()
    if curr_user == None:
        entry = Leaderboard(user=userID, highScore=score, date=date)
        db.session.add(entry)
        db.session.commit()
        return f"Score saved successfully. New high score of {score}!"
    elif score > curr_user._highScore:
        curr_user._highScore = score
        curr_user._date = date
        db.session.commit()
        return f"Score saved successfully. New high score of {score}!"
    else:
        db.session.commit()
        return "Score saved successfully. No new high score."


def run():
    app.run(host='0.0.0.0',port=8069)

initUserTable()
initLeaderboard()
initScores()
run()