import os
from flask import Flask, render_template, request, redirect, url_for, make_response
from flask_socketio import SocketIO, emit, join_room
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker,scoped_session
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
from flask_sqlalchemy import SQLAlchemy
from models import *
import uuid
from PIL import Image

app = Flask(__name__)

#Getting Environment Variables for the Server
if os.getenv("DATABASE_URL") is None:
    raise Exception ("Server not setup")

#Configuration of the Application
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {'pool_size':15 ,'max_overflow': -1}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['UPLOAD_FOLDER'] = os.getenv("UPLOAD_FOLDER")


#Setting Up SocketIO
socketio = SocketIO(app)
login = LoginManager(app)

@login.user_loader
def load_user(userid):
    return User.query.get(int(userid))

#Connecting to the Server
db = SQLAlchemy()
db.init_app(app)

@app.route("/")
def index():
    if current_user.is_authenticated:
        try:
            id = int(request.cookies.get('channel'))
            return redirect(url_for('channel', id = id))

        except:
            return redirect(url_for('mychannels'))
    
    return render_template("signin.html")

@app.route("/signin", methods = ['GET', 'POST'])
def signin():
    username = request.form.get("username")
    password = request.form.get("password")
    rememberme = request.form.get("rememberme")
    if rememberme != None:
        rememberme = True
    else:
        rememberme = False
    user = User.query.filter_by(username = username, password = password).first()

    if user is None:
        return render_template("status.html", page_title='Error', message="Incorrect Username or Password", button_name='Try Again',route_link='/')
    
    login_user(user,remember=rememberme)
    return redirect(url_for('mychannels'))

@app.route('/signup',methods = ['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template("signup.html")
    username = request.form.get("username")
    password = request.form.get("password")
    email = request.form.get("email")
    displayname = request.form.get("displayname")

    #Check if Email, Username or Displayname Already Exists
    user = User.query.filter_by(email=email).first()
    if user != None:
        return render_template("status.html", page_title='Error', message = "An account with this email address already exists, Please try using something else", button_name='Try Again', link='/signup')

    user = User.query.filter_by(username=username).first()
    if user != None:
        return render_template("status.html", page_title='Error', message = "The Username Already Exists, Please try using something else", button_name='Try Again', link='/signup')
    
    user = User.query.filter_by(displayname=displayname).first()
    if user != None:
        return render_template("status.html", page_title='Error', message = "The Displayname Already Exists, Please try using something else", button_name='Try Again', link='/signup')

    user = User(username=username,password=password,email=email,displayname=displayname)
    db.session.add(user)
    db.session.commit()

    return render_template("status.html", page_title='Success', message = "You have now signed up!", button_name='Sign In', route_link='/')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('logout.html', message='You have successfully been logged out of the application.', button_name = 'Sign In Again', route_link='/')

@app.route('/create_channel', methods = ['GET', 'POST'])
@login_required
def create_channel():
    if request.method == 'GET':
        id = current_user.get_id()
        users = User.query.filter(User.id !=id).all()
        return render_template('create_channel.html', users = users)
    
    channel_name = request.form.get("channelname")
    users = request.form.getlist("users")
    users.append(current_user.get_id())

    #Check if Channel Name Already Exists
    channel = Channel.query.filter_by(name = channel_name).first()
    if channel != None:
        return render_template("status.html", page_title='Error', message = "A Channel by this name already exists. Please choose a unique channel name.")

    #Create a New Channel
    channel = Channel(name=channel_name)
    db.session.add(channel)
    db.session.commit()

    #Add Users In a Channel
    for user in users:
        user_channel = User_Channel(channel_id = channel.id)
        user_channel.user_id = int(user)
        db.session.add(user_channel)
    db.session.commit()

    return render_template("status.html", page_title='Success', message = "New Channel Created!", button_name='Show All My Channels', route_link='/mychannels')

@app.route('/mychannels', methods = ['GET', 'POST'])
@login_required
def mychannels():
    if request.method == 'GET':
        id = current_user.get_id()
        my_channel = User_Channel.query.filter_by(user_id = id).all()
        #my_channel = User_Channel.query.with_entities(User_Channel.channel_id).filter_by(user_id = id).all()        
        channel_list = []
        for c in my_channel:
            channel_list.append(c.channel_id)

        channels = Channel.query.filter(Channel.id.in_(channel_list)).all()
        user = User.query.filter_by(id = id).first()
        displayname = user.displayname
        return render_template("mychannels.html", displayname = displayname, channels = channels)
    
@app.route('/joinchannel', methods = ['GET', 'POST'])
@login_required
def joinchannel():

    if request.method == 'GET':
        #Display All the Existing Unjoined Channels for the current_user
        user_id = int(current_user.get_id())
        joined_channels = User_Channel.query.with_entities(User_Channel.channel_id).filter_by(user_id = user_id).all()
        unjoined_channels = Channel.query.filter(~Channel.id.in_(joined_channels)).all()

        if unjoined_channels is None or len(unjoined_channels) < 1:
            return render_template("status.html", page_title = "No Channels", message = "No Other Channels to Join", button_name = "Create a New Channel", route_link = "/create_channel")
        
        else:
            return render_template("joinchannel.html", channels=unjoined_channels)
    
    elif request.method == 'POST':
        channel_id = int(request.form.get('id'))
        user_id = int(current_user.get_id())

        user_channel = User_Channel(user_id=user_id,channel_id=channel_id)
        db.session.add(user_channel)
        db.session.commit()

    return render_template("status.html", page_title="Channel Joined", message="You have joined the selected Channel.", button_name="My Channels" ,route_link ="mychannels")

@app.route('/channel/<int:id>', methods = ["GET", "POST"])
@login_required
def channel(id):
    id = int(id)
    channel = Channel.query.get(id)
    posts = Post.query.filter_by(channel_id=id).order_by(Post.timestamp).limit(100).all()
    namespace = f'/channel/{id}'
    resp = make_response(render_template("channel.html", message = f"You are on Channel {id}", channel = channel, namespace = namespace, posts = posts))
    resp.set_cookie('channel',f"{id}",86400)
    return resp 

@socketio.on("join")
def on_join(data):
    namespace = data['namespace']
    join_room(namespace)

@socketio.on("get message")
def get_msg(data):
    user_id = current_user.get_id()
    user = User.query.filter_by(id = user_id).first()
    namespace = data['namespace']
    channel_id = data['channel_id']
    msg = data['msg']
    post = Post(post=msg, user_id=user_id, channel_id=channel_id)
    db.session.add(post)
    db.session.commit()
    emit("send message", {"msg":msg, 'user':user.displayname, 'pic': user.profile_pic}, broadcast=True, room = namespace)

@app.route('/myprofile', methods=['GET', 'POST'])
@login_required
def myprofile():
    if request.method == 'GET':
        user_id = int(current_user.get_id())
        user = User.query.filter_by(id = user_id).first()
        return render_template('profile.html', user=user)
    
    if request.method == 'POST':
        user_id = int(current_user.get_id())
        profile_pic = request.files['profilepic']
        username = request.form.get('username')
        displayname = request.form.get('displayname')
        email = request.form.get('email')

        #Check if that username already exists
        check_username = User.query.with_entities(User.username).filter(and_(User.id != user_id, User.username == username)).first()
        if check_username != None:
            return render_template("status.html", page_title='Error', message = "An account with this username already exists, Please try using something else", button_name='Try Again', link='/myprofile')

        check_email = User.query.with_entities(User.email).filter(and_(User.id != user_id, User.email == email)).first()
        if check_email != None:
            return render_template("status.html", page_title='Error', message = "An account with this email address already exists, Please try using something else", button_name='Try Again', link='/myprofile')
        
        #See if a new profile picture was uploaded
        if profile_pic.filename == '':
            filename = 'default.jpg'
        else:
            filename = uuid.uuid1().hex.upper()[:10] + '.' +profile_pic.filename.rsplit('.',1)[-1]
            profile_pic.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            im = Image.open(os.path.join(os.getenv('UPLOAD_FOLDER'), filename))
            im_resized = im.resize((120,120))
            im_resized.save(os.path.join(os.getenv('UPLOAD_FOLDER'), filename))
        
        #Make all the Updates
        user = db.session.query(User).get(user_id)
        user.username = username
        user.email = email
        user.displayname = displayname
        user.profile_pic = filename
        db.session.commit()

        return render_template("status.html",page_title='Success', message = "Profile Successfully Updated", button_name='My Channels', route_link='/mychannels')