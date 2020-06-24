import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


db = SQLAlchemy(app)
db.init_app(app)

class User(UserMixin, db.Model):
    __tablename__="user"
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String, unique=True, nullable=False)
    email = db.Column(db.String, unique=True, nullable=False)
    displayname = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    profile_pic = db.Column(db.String, nullable=True, default='default.jpg')
    posts = db.relationship('Post', backref='user', lazy=True)
    channels = db.relationship('User_Channel', backref='user', lazy=True)

    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password,password)
    def __repr__(self):
        return "<User {}>".format(self.username)

class Channel(db.Model):
    __tablename__="channel"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    created = db.Column(db.DateTime, default = datetime.datetime.utcnow)
    user_channel = db.relationship('User_Channel', backref='channel', lazy=True)

    def __repr__(self):
        return f"<Channel {self.name}>"

class User_Channel(db.Model):
    __tablename__="user_channel"
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    channel_id = db.Column(db.Integer, db.ForeignKey('channel.id'), primary_key=True)

class Post(db.Model):
    __tablename__='post'
    id = db.Column(db.Integer, primary_key=True)
    post = db.Column(db.String(300),nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    channel_id = db.Column(db.Integer, db.ForeignKey('channel.id'))
    timestamp = db.Column(db.DateTime, index=True, default = datetime.datetime.utcnow)

    def __repr__(self):
        return f"<Post - User - {self.user_id} Channel - {self.channel_id}>"


db.create_all()