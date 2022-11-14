from .database import db

class user(db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.Integer, autoincrement= True, primary_key= True)
    user_name = db.Column(db.String, nullable=False, unique=True)
    password = db.Column(db.String, nullable=False)

class logs(db.Model):
    __tablename__ = 'logs'
    log_id = db.Column(db.Integer, autoincrement= True, primary_key=True)
    datetime = db.Column(db.String, nullable=False)
    value = db.Column(db.String, nullable = False)
    notes = db.Column(db.String, nullable = True)
    
class tracker(db.Model):
    __tablename__ = 'tracker'
    tracker_id = db.Column(db.Integer, autoincrement= True, primary_key=True)
    tracker_name = db.Column(db.String, nullable = False, unique = True)
    tracker_type = db.Column(db.String, nullable = False)
    tracker_settings = db.Column(db.String, nullable = False)
class assignment(db.Model):
    __tablename__ = 'assignment'
    assignment_id =  db.Column(db.Integer, autoincrement= True, primary_key=True)
    tracker_id = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    log_id = db.Column(db.String, nullable=False)