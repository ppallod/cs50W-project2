# Project 2 - Flack

## CS50 - Web Programming with Python and JavaScript

In this project, I've created an Online Messaging service similar to Slack. Flack is a web application that demonstrates the use of Flask-SocketIO on the server side and SocketIO on the client side, to have a real-time communication among several users. 

#### WorkFlow 

Users will be able to sign up on this application, join existing channels(chatrooms) if available or create their own new channels. Once they enter a channel, they can send and receive text messages in real-time without having to reload the webpage. The main application is inside `application.py`, it uses the following environment variables - 

* `DATABASE_URL` - The URI for database connection.
* `UPLOAD_FOLDER` - The directory for storing `.jpg` files for users profile pictures. 

All the python dependencies are present in `requirements.txt`, `html` resources are contained in `templates` folder and the `jpg` files are inside `static/img` folder.

#### Models

This application uses Object Relational Mapping (ORM) by making use of `flask_sqlalchemy` and `sqlalchemy.orm` for handling the data. It uses the following models - `user`, `channel`, `user_channel`, `post`. All these models are defined in `models.py` file.

#### Sign Up & Sign In

When a user visits the website for the first time, they will be asked to sign up on the web application. For signing up, they would have to provide - `email address`, `username`, `password` & `displayname`. Email Address, username & displayname have to be unique for each user. When a user signs in and checks the `remember me` button, the server would keep that user logged in for future use.

Moreover, if a user is already authenticated and returns to the application at `\` route, they will be redirected to their most recently active channel. Finally, a user can logout of the application by clicking the logout button. I have used `@login_required` decorator so that a user can only access the `\logout` route if they are already signed in.

* `html` - `signup.html`, `signin.html`.
* `routes` - `@app.route('/signup')`, `@app.route("/signin")`, `@app.route("/")`, `@app.route('/logout')`.

#### Channels

Users are allowed to create their own channel or join an existing channel. Here again, I have used the `@login_required` decorator so make sure that the user is logged in for accessing channels. When a user visits one of the channels `/channel/<int:id>` let's say the one with `id=1`, the route for that channel would be dynamically generated to be `/channel/1`. Whenever a user visits a channel, they are joined to the common socket have the same `namespace` using `@socketio.on("join")`. Once they are on the channel, server is listening for events from all the clients via `@socketio.on("get message")`. When a new message is received, the socket would emit the event `emit("send message")` which will be used by the SocketIO with the JavaScript in `channel.html` on the client side to display new messages on the webpage.

* `html` - `channel.html`, `create_channel.html`, `join_channel.html`, `mychannels.html`.
* `routes` - `@app.route('/channel/<int:id>')`,`@app.route('/create_channel')`, `@app.route('/mychannels')`, `@app.route('/joinchannel')`.

#### Profile

A user can update their profile details by clicking the `myprofile` button on the `\mychannels` route. They can change their - `email address`, `username`, `displayname` & `profile picture`. By default the application uses `default.jpg` from the `static/img` directory, but the user can update that.

* `html` - `profile.html`.
* `routes` - `@app.route('/myprofile')`.

#### Layout, Status

To minimize the number of html pages and css files, I have used `bootstrap` for keeping my html styling modern and clean. I've used Jinja templating to inherit this style in most of the html pages. Finally, to show `success` & `error` messages, I have used `status.html` by dynamically changing the title, heading, messages and buttons.

* `html` - `layout.html`, `status.html`

