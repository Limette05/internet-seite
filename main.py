from datetime import datetime
from flask import Flask, render_template, request, session, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user, login_remembered
from flask_wtf import FlaskForm
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, send, emit, join_room, leave_room, send, SocketIO
import random
from wtforms import StringField, PasswordField, SubmitField, EmailField
from wtforms.validators import InputRequired, Length, ValidationError
from sqlalchemy import Integer, String, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import os

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)


app = Flask(__name__, static_folder="static")
socketio = SocketIO(app)
bcrypt = Bcrypt(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
db.init_app(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# neue Nachricht -> neue Konversation(username)
# add 
#
#

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_ip = db.Column(db.String(200), nullable=True)
    username = db.Column(db.String(200), nullable=True)
    content = db.Column(db.String(500), nullable=True)
    conversation = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime(), default=datetime.now)

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    owner = db.Column(db.String, nullable=False) # ist die owner.id
    title = db.Column(db.String, nullable=False) # wird später festgelegt als owner.username
    last_editor = db.Column(db.String, nullable=False)  # Letzter Bearbeiter, wird erstmals als "leer" eingetragen
    state = db.Column(db.Integer, nullable=False, default=0)  # 0=Offen, 1=In Bearbeitung, 2=Fertig
    created_at = db.Column(db.DateTime(), default=datetime.now)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), nullable=False, unique=True)
    username = db.Column(db.String(200), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    team_status = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(), default=datetime.now)

class RegisterForm(FlaskForm):
    email = EmailField(validators=[InputRequired()], render_kw={"placeholder":"E-Mail"})
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Nutzername"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Passwort"})
    submit = SubmitField("Registrieren")

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()

        if existing_user_username:
            raise ValidationError("Nutzername bereits vergeben")
    
    def validate_email(self, email):
        existing_user_email = User.query.filter_by(email=email.data).first()

        if existing_user_email:
            raise ValidationError("E-Mail bereits vergeben")
    
class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Nutzername"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Passwort"})
    submit = SubmitField("Anmelden")


with app.app_context():
    db.create_all()

@app.route("/", methods=['GET','POST'])
def index():
    login_state = False
    if current_user.is_authenticated:
        login_state = True
    # todo
    # make request for messages when clicking on select conversation
    # when opening chat give plus-chat and select existing-chat
    return render_template("index.html", login_state=login_state)

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    join_room(room)

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

@socketio.on("message")
def message(data):
    room = session.get("room")
    if not room:
        return
    new_message = Message(
            user_ip = request.remote_addr,
            username = current_user.username,
            content = data["data"],
            conversation = room
        )
    db.session.add(new_message)
    db.session.commit()
    current_time = datetime.now()
    content = {
        "name": session.get("name"),
        "message": data["data"],
        "created_at": current_time.strftime('%d. %b | %H:%M Uhr')
    }
    send(content, to=room)


@app.route("/chat-redirect", methods=["POST","GET"])
def chat_redirect():
    # check if conversation exists and give parameters
    # if not create conversation
    conversations = []
    user = User.query.filter_by(id=current_user.id).first()
    room = Conversation.query.filter_by(owner=user.id).first()
    if room:
        session["room"] = room.id

    session["name"] = user.username
    team_status = user.team_status
    if team_status > 0:
        raw_conversations = Conversation.query.all()
        for conv in raw_conversations:
            conversations.append(conv)

        get_conv_id = request.args.get('conv_id')
        if get_conv_id:
            room = Conversation.query.filter_by(id=get_conv_id).first()
            session["room"] = room.id
    if not room and team_status == 0:
        owner =  User.query.filter_by(id=current_user.id).first()
        new_conversation = Conversation(
            owner = owner.id,
            title = owner.username,
            last_editor = ""
        )
        db.session.add(new_conversation)
        db.session.commit()
        room = Conversation.query.filter_by(owner=owner.id).first()
        session["room"] = room.id
    dict_messages = []
    if room:
        messages = Message.query.filter_by(conversation=room.id).all()
        for msg in messages:
            dict_messages.append({
                'username': msg.username,
                'content': msg.content,
                'created_at': msg.created_at.strftime('%d. %b | %H:%M Uhr')
                })

    return render_template("chat-redirect.html", username=user.username, messages=dict_messages,
                            team_status=team_status, conversations=conversations)


@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if not current_user.is_authenticated:
        return redirect("/login")
    user = User.query.filter_by(id=current_user.id).first()
    team_status = user.team_status
    return render_template("dashboard.html", team_status=team_status)

@app.route("/profile", methods=['GET','POST'])
def team_chat():
    # full size chat with link back to chats
    email = current_user.email
    username = current_user.username
    return render_template("profile.html", email=email, username=username)

@app.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm()
    error = ""
    if form.validate_on_submit():
        error = "Nutzer nicht bekannt!"
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            error = "Falsches Passwort!"
            if bcrypt.check_password_hash(user.password, form.password.data):
                remember = request.form.get("rememberme", False)
                login_user(user, remember=remember)
                return redirect(url_for("dashboard"))
    return render_template("login_page.html", form=form, error=error)

@app.route("/register", methods=["GET","POST"])
def register():
    form = RegisterForm()
    username = form.username.data
    team_status = 0
    team_list = ["Lena Langenfels", "Jens Steinmetz", "Christian Rymas", "Andrea Roth Wiegand", "Jens Richter"]
    admin_list = ["Christian Roth", "Michael Fix", "Ilka Roth", "Kerstin Roth"]
    if username in team_list:
        team_status = 1
    elif username in admin_list:
        team_status = 2
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        new_user = User(email=form.email.data, username=username, password=hashed_password, team_status=team_status)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template("register_page.html", form=form)

@app.route("/sortiment")
def sortiment():
    return render_template("sortiment.html")

@app.route("/about-us")
def about_us():
    return render_template("about_us.html")

@app.route("/logout", methods=['GET','POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/forgot_password")
def forgot_password():
    return render_template("forgot_password.html")


if __name__ == "__main__":
    app.run(debug=True, host="45.93.249.124")