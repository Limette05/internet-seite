from datetime import datetime
import random
import os
import string
import cv2
from flask import Flask, render_template, request, session, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user, login_remembered
from flask_mail import Mail, Message as mail_msg
from flask_wtf import FlaskForm
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO, send, emit, join_room, leave_room, send, SocketIO
from wtforms import StringField, PasswordField, SubmitField, EmailField
from wtforms.validators import InputRequired, Length, ValidationError
from sqlalchemy import Integer, String, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)
host = "localhost" # your IP address or Domain (str)

app = Flask(__name__, static_folder="static")
socketio = SocketIO(app)
bcrypt = Bcrypt(app)
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'your@email.com'
app.config['MAIL_PASSWORD'] = 'your app password'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
SECRET_KEY = os.urandom(32)
app.config['SECRET_KEY'] = SECRET_KEY
db.init_app(app)

admin_list = ["Limette","Admin"]


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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
    new_msg = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime(), default=datetime.now)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), nullable=False, unique=True)
    username = db.Column(db.String(200), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    team_status = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime(), default=datetime.now)
    verified = db.Column(db.Integer, nullable=False)

class ChangeUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(200), nullable=False, unique=True)
    password_code = db.Column(db.String, nullable=True)
    deletion_code = db.Column(db.String, nullable=True)

class Werbung(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    active = db.Column(db.Integer, nullable=False)
    creator = db.Column(db.String, nullable=False) # username des Creators
    editor = db.Column(db.String, nullable=False) # username des Editors
    image = db.Column(db.String, nullable=False) # Pfad zum Bild
    title = db.Column(db.String(64), nullable=False, unique=True)
    description = db.Column(db.JSON, nullable=False)
    start = db.Column(db.String(), nullable=True)
    end = db.Column(db.String(), nullable=True)

class RegisterForm(FlaskForm):
    email = EmailField(validators=[InputRequired()], render_kw={"placeholder":"E-Mail"})
    username = StringField(validators=[InputRequired(), Length(min=4, max=32)], render_kw={"placeholder": "Nutzername"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=64)], render_kw={"placeholder": "Passwort"})
    submit = SubmitField("Registrieren")

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()

        if existing_user_username:
            return("Nutzername bereits vergeben")
    
    def validate_email(self, email):
        existing_user_email = User.query.filter_by(email=email.data).first()

        if existing_user_email:
            return("E-Mail bereits vergeben")
    
class LoginForm(FlaskForm):
    email = EmailField(validators=[InputRequired()], render_kw={"placeholder":"E-Mail"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=64)], render_kw={"placeholder": "Passwort"})
    submit = SubmitField("Anmelden")


with app.app_context():
    db.create_all()

@app.route("/admin", methods=["GET","POST"])
def admin():
    if not current_user.is_authenticated:
        return redirect("/login")
    if current_user.verified != 1:
        return redirect("/verify")
    user = User.query.filter_by(id=current_user.id).first()
    if user.team_status != 2:
        return redirect("/")
    msg = ""
    userList = User.query.filter_by(verified=1).all()
    userID = request.args.get("userID")
    editUser = None
    if userID:
        editUser = User.query.filter_by(id=userID).first()
    if request.method == "POST":
        edit_user = request.form.get("edit-user", False)
        edit_team_status = request.form.get("change-team-status", False)
        if edit_user:
            msg = ["Geändert: "]
            if edit_team_status:
                editUser.team_status = int(edit_team_status)
                msg.append(f"Team-Status: {edit_team_status}")
    return render_template("admin.html", msg=msg, team_status=user.team_status, 
                           userList=userList, editUser=editUser)

@app.route("/werbung", methods=['GET','POST'])
def werbung():
    if not current_user.is_authenticated:
        return redirect("/login")
    if current_user.verified != 1:
        return redirect("/verify")
    user = User.query.filter_by(id=current_user.id).first()
    if user.team_status == 0:
        return redirect("/")
    msg = ""
    editor = ""
    werbungen = Werbung.query.all()
    returned_werbung = None
    current_werbung = None
    edit = request.args.get("werbung_ID")
    current_werbung_start = None
    current_werbung_end = None
    if edit:
        current_werbung = Werbung.query.filter_by(id=edit).first()
        if current_werbung.start:
            current_werbung_start = datetime.strptime(current_werbung.start, '%d.%m.%Y').strftime('%Y-%m-%d')
        if current_werbung.end:
            current_werbung_end = datetime.strptime(current_werbung.end, '%d.%m.%Y').strftime('%Y-%m-%d')
    if request.method == "POST":
        title = request.form.get("werbung-title", False)
        description = request.form.get("werbung-description", False)
        description = description.split("\r\n")
        start = request.form.get("werbung-start", False)
        end = request.form.get("werbung-end", False)
        if start:
            start = datetime.strptime(start, '%Y-%m-%d').date()
            start = start.strftime('%d.%m.%Y')
        if end:
            end = datetime.strptime(end, '%Y-%m-%d').date()
            end = end.strftime('%d.%m.%Y')
        image = ""
        file = request.files['werbung-image']
        if file:
            file.save(f"static/html addons/werbung-img/{file.filename}")
            image = f"static/html addons/werbung-img/{file.filename}"
            check_im_size = cv2.imread(image)
            h, w, _ = check_im_size.shape
            if h != 500 or w != 500:
                os.remove(image)
                returned_werbung = {"title":title,"description":description,"start":start,"end":end,"image":None}
                return render_template("werbung.html", msg="Bildgröße muss 500x500 Pixeln entsprechen!", team_status=user.team_status, werbungen=werbungen, current_werbung=current_werbung, 
                                current_werbung_start=current_werbung_start, current_werbung_end=current_werbung_end, returned_werbung=returned_werbung)
        #if start before datetime.now:
            #active = 1
        check_titles = Werbung.query.filter_by(title=title).first()
        if check_titles:
            if not current_werbung:
                returned_werbung = {"title":title,"description":description,"start":start,"end":end,"image":image}
                return render_template("werbung.html", msg="Titel existiert bereits! Bearbeiten? In Liste auswählen!", team_status=user.team_status, werbungen=werbungen, current_werbung=current_werbung, 
                           current_werbung_start=current_werbung_start, current_werbung_end=current_werbung_end, returned_werbung=returned_werbung)
        if current_werbung:
                active = request.form.get("werbung-active")
                delete = request.form.get("werbung-löschen")
                if active is not None:
                    if current_werbung.active:
                        current_werbung.active = 0
                        msg = f"Deaktiviert: {current_werbung.title}"
                    else:
                        current_werbung.active = 1
                        msg = f"Aktiviert: {current_werbung.title}"
                elif delete is not None:
                    msg = f"Unwiderruflich gelöscht: {current_werbung.title}"
                    db.session.delete(current_werbung)
                else:
                    if image:
                        current_werbung.image = image
                    current_werbung.title = title
                    current_werbung.description = description
                    current_werbung.editor = current_user.username
                    current_werbung.start = start
                    current_werbung.end = end
                    msg = f"Bearbeitet: {title}"
        else:
            msg = f"Erstellt: {title}"
            new_werbung = Werbung(title=title, description=description, image=image, active=1, creator = current_user.username, editor=editor, start=start, end=end)
            db.session.add(new_werbung)
        db.session.commit()
    return render_template("werbung.html", msg=msg, team_status=user.team_status, werbungen=werbungen,current_werbung=current_werbung, 
                           current_werbung_start=current_werbung_start, current_werbung_end=current_werbung_end, returned_werbung=returned_werbung)


@app.route("/", methods=['GET','POST'])
def index():
    login_state = False
    team_status = 0
    if current_user.is_authenticated:
        login_state = True
        team_status = current_user.team_status
    werbung = Werbung.query.filter_by(active=1).all()
    return render_template("index.html", login_state=login_state, werbung=werbung, team_status=team_status)

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

@socketio.on("change_conv_state")
def change_conv_state(data):
    room = session.get("room")
    new_state = data["data"]
    conv = Conversation.query.filter_by(id=room).first()
    conv.state = new_state
    db.session.commit()
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
    conversation = Conversation.query.filter_by(id=room).first()
    if current_user.team_status == 0:
        conversation.new_msg = 1
    else:
        conversation.new_msg = 0
        conversation.last_editor = current_user.username
    db.session.commit()
    current_time = datetime.now()
    content = {
        "name": session.get("name"),
        "message": data["data"],
        "created_at": current_time.strftime('%d. %b | %H:%M Uhr')
    }
    send(content, to=room)


def sortByNewMsg(conv):
  return conv.new_msg

def sortByName(conv):
  return conv.title

@app.route("/chat-redirect", methods=["POST","GET"])
def chat_redirect():
    if not current_user.is_authenticated:
        return redirect("/login")
    if current_user.verified != 1:
        return redirect("/verify")
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
        conversations.sort(key=sortByName)
        conversations.sort(reverse=True, key=sortByNewMsg)

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
                            team_status=team_status, conversations=conversations, current_conversation=room, host=host)


@app.route("/dashboard", methods=["GET","POST"])
def dashboard():
    if not current_user.is_authenticated:
        return redirect("/login")
    if current_user.verified != 1:
        return redirect("/verify")
    user = User.query.filter_by(id=current_user.id).first()
    team_status = user.team_status
    return render_template("dashboard.html", team_status=team_status)

@app.route("/profile", methods=['GET','POST'])
def team_chat():
    email = current_user.email
    username = current_user.username
    return render_template("profile.html", email=email, username=username)

@app.route("/delete_acc", methods=["GET","POST"])
def delete_acc():
    """after click on 'delete profile' in /profile
    you are sent here. If deletetion_code doesn't exist it's sent."""
    if not current_user.is_authenticated:
        return redirect("/login")
    if current_user.verified != 1:
        return redirect("/verify")
    error = ""
    email_sent = False
    data = ChangeUser.query.filter_by(email=current_user.email).first()
    user = User.query.filter_by(email=current_user.email).first()
    if not data:
        data = ChangeUser(email=user.email, password_code="", deletion_code="")
        db.session.add(data)
        db.session.commit()
    if data.deletion_code:
        """ask for verification"""
        email_sent = data.email
        if request.method == "POST":
            code = request.form.get('post_deletion_code', False)
            if data.deletion_code == str(code):
                conversations = Conversation.query.filter_by(owner=user.id).all()
                for conv in conversations:
                    db.session.delete(conv)
                    messages = Message.query.filter_by(conversation=conv.id).all()
                    for msg in messages:
                        db.session.delete(msg)
                db.session.delete(user)
                db.session.commit()
                logout_user()
                return redirect("/login")
            else:
                error = "Code falsch eingegeben!"
    else:
        email_sent = data.email
        send_delete_acc(data)
        
    return render_template("delete_acc.html", error=error, email_sent=email_sent)

def send_delete_acc(data):
    code = "".join(random.choice(string.ascii_uppercase+string.digits) for _ in range(12))
    data.deletion_code = code
    db.session.commit()
    msg = mail_msg("Account löschen", sender="noreply.limette05@gmail.com",
                   recipients=[data.email])
    msg.body = f"Möchten Sie Ihren Account wirklich löschen?\n\nAlle Daten werden unwiderruflich gelöscht!\n\n"
    msg.body += f"Ihr Eingabe-Code:\n{code}\n\n\n"
    msg.body += f"Das waren Sie nicht?\n"
    msg.body += f"Dann ignorieren Sie diese Nachricht einfach."
    mail.send(msg)
    return("E-Mail wurde gesendet! Überprüfe dein Postfach.")


def send_password_reset(data):
    code = "".join(random.choice(string.ascii_uppercase+string.digits) for _ in range(24))
    data.password_code = code
    db.session.commit()
    link = f"http://{host}:5000/new_password?code={code}"
    msg = mail_msg("Passwort zurücksetzen", sender="noreply.limette05@gmail.com",
                   recipients=[data.email])
    msg.body = f"Über folgenden Link können Sie ihr Passwort zurücksetzen:\n{link}\n\nDas sind Sie nicht?\nDann ignorieren Sie diese Nachricht einfach."
    mail.send(msg)
    return("E-Mail wurde gesendet! Überprüfe dein Postfach.")

def send_verification(user):
    code = random.randint(11111111,99999999)
    user.verified = code
    db.session.commit()
    link = f"http://{host}:5000/verify?verify={code}"
    msg = mail_msg("Verifizieren Sie ihre Anmeldung", sender="noreply.limette05@gmail.com",
                   recipients=[user.email])
    msg.body = f"Hallo {user.username}!\nÖffnen Sie diesen Link, um ihren Account zu verifizieren:\n{link}\n\nOder geben Sie den Code im Eingabefeld ein:\n{code}\n\nDas sind Sie nicht?\nDann ignorieren Sie diese Nachricht einfach."
    mail.send(msg)
    return("E-Mail wurde gesendet! Überprüfe dein Postfach.")

@app.route("/new_password", methods=["GET","POST"])
def new_password():
    get_code = request.args.get('code')
    set_new_password = False
    error = ""
    if not get_code:
        if current_user.is_authenticated:
            pass
        else:
            return redirect("/")
    code_verified = ChangeUser.query.filter_by(password_code=get_code).first()
    if code_verified or current_user.is_authenticated:
        set_new_password = True
        if current_user.is_authenticated:
            user = current_user
        else:
            user = User.query.filter_by(email=code_verified.email).first()
            db.session.delete(code_verified)
        if request.method == "POST":
            new_password1 = request.form.get("new-password1", False)
            new_password2 = request.form.get("new-password2", False)
            if new_password1 != new_password2:
                error = "Passwörter stimmen nicht überein!"
            else:
                hashed_password = bcrypt.generate_password_hash(new_password1)
                user.password = hashed_password
                db.session.commit()
                login_user(user)
                return redirect("/dashboard")
    return render_template("new_password.html", set_new_password=set_new_password, error=error)

@app.route("/verify", methods=["GET","POST"])
def verify():
    if not current_user.is_authenticated:
        return redirect("/login")
    user = User.query.filter_by(id=current_user.id).first()
    error = False
    email_sent = ""
    if user.verified > 1:
        email_sent = user.email
    need_verify = True
    if user.verified == 1:
        need_verify = False 
        return redirect("/dashboard")
    get_code = request.args.get('verify')
    if get_code:
        need_verify = False
        if str(user.verified) == get_code:
            user.verified = 1
            db.session.commit()
            return redirect("/dashboard")
        else:
            error = True
    
    if request.method == "POST":
        get_code_entry = request.form.get("post_code", False)
        if get_code_entry:
            if str(user.verified) == get_code_entry:
                user.verified = 1
                db.session.commit()
                return redirect("/dashboard")
            else:
                error = True
        else:
            send_verification(user)
    return render_template("verify.html", error=error, email_sent=email_sent, need_verify=need_verify)

@app.route("/login", methods=["GET","POST"])
def login():
    form = LoginForm()
    error = ""
    if form.validate_on_submit():
        error = "Nutzer nicht bekannt!"
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            error = "Falsches Passwort!"
            if bcrypt.check_password_hash(user.password, form.password.data):
                remember = request.form.get("rememberme", False)
                login_user(user, remember=remember)
                return redirect(url_for("dashboard"))
    return render_template("login_page.html", form=form, error=error)

@app.route("/register", methods=["GET","POST"])
def register():
    error = ""
    form = RegisterForm()
    username = form.username.data
    team_status = 0
    if username in admin_list:  # edit your admin_list
        team_status = 2
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data)
        code = random.randint(11111111,99999999)
        email = form.email.data
        error = form.validate_email(form.email)
        if not error:
            error = form.validate_username(form.username)
        if error:
            return render_template("register_page.html", form=form, error=error)
        new_user = User(email=email, username=username, password=hashed_password, team_status=team_status, verified=code)
        send_verification(new_user)
        db.session.add(new_user)
        db.session.commit()
        remember = request.form.get("rememberme", False)
        login_user(new_user, remember=remember)
        return redirect(url_for("dashboard"))
    return render_template("register_page.html", form=form, error=error)

@app.route("/sortiment")
def sortiment():
    return render_template("sortiment.html")

@app.route("/about-us")
def about_us():
    return render_template("about_us.html")

@app.route("/logout", methods=['GET','POST'])
def logout():
    if not current_user.is_authenticated:
        return redirect("/login")
    logout_user()
    return redirect(url_for('login'))

@app.route("/forgot_password", methods=["GET","POST"])
def forgot_password():
    sent = ""
    error = ""
    if request.method == "POST":
        get_email = request.form.get("reset-email", False)
        user = User.query.filter_by(email=get_email).first()
        if user:
            data = ChangeUser(email=get_email, password_code="", deletion_code="")
            db.session.add(data)
            db.session.commit()
            send_password_reset(data)
            sent = get_email
        else:
            error = f"Die E-Mail Adresse {get_email} wurde nicht gefunden."
    return render_template("forgot_password.html", sent=sent, error=error)


if __name__ == "__main__":
    app.run(host=host)