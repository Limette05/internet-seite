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


app = Flask(__name__, static_folder="C:/Users/micha/Documents/internet-seite/static")
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
    owner = db.Column(db.String, nullable=False)
    title = db.Column(db.String, nullable=False, default="Neue Konversation")
    team_title = db.Column(db.String, nullable=False, default="Team-Konversation")
    last_editor = db.Column(db.String, nullable=True)  # Letzter Bearbeiter
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

    # todo
    # make request for messages when clicking on select conversation
    # when opening chat give plus-chat and select existing-chat
    return render_template("index.html")

@app.route("/get_conversations", methods=["GET"])
def get_conversations():
    if current_user.is_authenticated:
        conversations = Conversation.query.filter_by(owner=current_user.id).all()
        return jsonify([{
            "title": conversation.title,
            "id": conversation.id
        } for conversation in conversations])
    else:
        """Load private conversation. existing?"""
        conversation = Conversation.query.filter_by(owner=request.remote_addr)
        if conversation:
            return jsonify({"title": conversation.title,
                        "id": conversation.id})

@app.route("/send_message", methods=["POST"])
def send_message():
    if request.method == "POST":
        name = "Gast"
        conversation = request.remote_addr
        if current_user.is_authenticated:
            name = current_user.username
            conversation = current_user.id
        new_message = Message(
            user_ip = request.remote_addr,
            username = name,
            content = request.json['content'],
            conversation = conversation
        )
        db.session.add(new_message)
        db.session.commit()
    messages = Message.query.filter_by(conversation=conversation).order_by(Message.created_at).all()
    return jsonify([{
        'username': msg.username,
        'content': msg.content,
        'created_at': msg.created_at.strftime('%d. %b | %H:%M Uhr')
    } for msg in messages])


@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if not current_user.is_authenticated:
        return redirect("/login")
    name = current_user.username
    user = User.query.filter_by(username=name).all()
    team_status = user[0].team_status
    if team_status == 1:
        return redirect("/team_dashboard")
    elif team_status == 2:
        return redirect("/admin_dashboard")
    return render_template("dashboard.html")

@app.route("/team_dashboard", methods=['GET','POST'])
def team_dashboard():
    # link to team_chats
    if not current_user.is_authenticated:
        return redirect("/login")
    name = current_user.username
    user = User.query.filter_by(username=name).all()
    team_status = user[0].team_status
    if not team_status >= 1:
        return("Zugriff verweigert!")
    return render_template("team_dashboard.html")

@app.route("/admin_dashboard", methods=['GET','POST'])
def admin_dashboard():
    # link to team_chats
    if not current_user.is_authenticated:
        return redirect("/login")
    name = current_user.username
    user = User.query.filter_by(username=name).all()
    team_status = user[0].team_status
    if not team_status == 2:
        return("Zugriff verweigert!")
    return render_template("admin_dashboard.html")

@app.route("/team_chats", methods=['GET','POST'])
def team_chats():
    # display all conversations, filter_by(state)
    # show editable conversation name !Conversation_token is permanent until deletion
    # show username (guest = Gast#IP_ADDRESS)
    # show created_at
    # show state with buttons to manage state
    return render_template("team_chats.html")

@app.route("/team_chat", methods=['GET','POST'])
def team_chat():
    # full size chat with link back to chats
    return render_template("team_chat.html")

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
    team_list = ["Michael Fix", "Lena Langenfels"]
    admin_list = ["Dr. Christian Roth"]
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


@socketio.on("message")
def message(data):
    print(f"\n\n{data}\n\n")
    send(data)

if __name__ == "__main__":
    app.run(debug=True)