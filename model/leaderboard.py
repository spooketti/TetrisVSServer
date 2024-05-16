from init import db, app
import time
from werkzeug.security import check_password_hash,generate_password_hash

class Leaderboard(db.Model):
    __tablename__ = "leaderboard"
    user = db.Column(db.Integer,db.ForeignKey('users.id'))
    id = db.Column(db.Integer,primary_key=True)
    score = db.Column(db.Integer)
    date = db.Column(db.Text,default=time.time())
      
    
def initLeaderboard():
    with app.app_context():
        db.create_all()