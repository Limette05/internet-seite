from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__, static_folder="C:/Users/micha/Documents/internet-seite/static")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///db.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(200), nullable=True)
    user_name = db.Column(db.String(200), nullable=True)
    content = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)


with app.app_context():
    db.create_all()

@app.route("/<name>", methods=['GET','POST'])
def index(name):
    if request.method == "POST":
        new_message = Message(
            user_id = request.remote_addr,
            user_name = name,
            content = request.form['content'],
        )
        db.session.add(new_message)
        db.session.commit()
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("login_page.html")

@app.route("/sortiment")
def sortiment():
    return render_template("sortiment.html")

@app.route("/über-uns")
def about_us():
    return render_template("about_us.html")


if __name__ == "__main__":
    app.run(debug=True)