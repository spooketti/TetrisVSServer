from init import db, app
import time
from werkzeug.security import check_password_hash,generate_password_hash

    

class Leaderboard(db.Model):
    __tablename__ = "leaderboard"
    user = db.Column(db.Integer,db.ForeignKey('users.id'))
    id = db.Column(db.Integer,primary_key=True)
    highScore = db.Column(db.Integer)
    date = db.Column(db.Text,default=time.time())
    
    def update(self, newScore, date):
        if newScore > self.highScore:
            self.highScore = newScore
            self.date = date
            return True
        else:
            return False
    def read(self):
        return {
            'user': self.user,
            'highScore': self.highScore,
            'date': self.date
        }


class Scores(db.Model):
    __tablename__ = "scores"
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.Integer, db.ForeignKey('users.id'))
    score = db.Column(db.Integer)
    date = db.Column(db.Text,default=time.time())


def initLeaderboard():
    with app.app_context():
        db.create_all()

def initScores():
    with app.app_context():
        db.create_all()