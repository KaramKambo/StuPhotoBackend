from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
import os
import base64
import json
from random import randrange

# Initialize Flask app and SQLAlchemy
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

db = SQLAlchemy(app)

# Define the Post class to manage actions in 'posts' table, with a relationship to 'users' table
class Post(db.Model):
    __tablename__ = 'posts'

    id = db.Column(db.Integer, primary_key=True)
    note = db.Column(db.Text, nullable=False)
    image = db.Column(db.String, nullable=True)  # Modified to accept base64 encoded images
    userID = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __init__(self, id, note, image):
        self.userID = id
        self.note = note
        self.image = image

    def save_image(self, image_data):
        self.image = image_data
        db.session.commit()

    def __repr__(self):
        return f"Post(id={self.id}, userID={self.userID}, note={self.note}, image={self.image})"

# Define the User class
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    uid = db.Column(db.String(255), unique=True, nullable=False)
    _password = db.Column(db.String(255), nullable=False)
    dob = db.Column(db.Date)

    posts = db.relationship("Post", cascade='all, delete', backref='user', lazy=True)

    def __init__(self, name, uid, password="123qwerty", dob=date.today()):
        self.name = name
        self.uid = uid
        self.set_password(password)
        self.dob = dob

    @property
    def password(self):
        return self._password[0:10] + "..."

    def set_password(self, password):
        self._password = generate_password_hash(password, "pbkdf2:sha256", salt_length=10)

    def is_password(self, password):
        return check_password_hash(self._password, password)

    @property
    def age(self):
        today = date.today()
        return today.year - self.dob.year - ((today.month, today.day) < (self.dob.month, self.dob.day))

# Endpoint for uploading images
@app.route('/upload_image', methods=['POST'])
def upload_image():
    data = request.json
    user_id = data.get('user_id')
    note = data.get('note')
    image_data = data.get('image')

    # Create a new Post object to store the image
    post = Post(user_id, note, image_data)
    post.save_image(image_data)

    return "Image uploaded successfully"

# Endpoint for registering users
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name')
    uid = data.get('uid')
    password = data.get('password')
    dob = data.get('dob')

    user = User(name, uid, password, dob)
    db.session.add(user)
    db.session.commit()

    return "User registered successfully"

# Initialize the database with some test data
@app.before_first_request
def init_db():
    db.create_all()
    # Build your test data
    with app.app_context():
        u1 = User(name='Thomas Edison', uid='toby', password='123toby', dob=date(1847, 2, 11))
        u2 = User(name='Nicholas Tesla', uid='niko', password='123niko', dob=date(1856, 7, 10))
        u3 = User(name='Alexander Graham Bell', uid='lex')
        u4 = User(name='Grace Hopper', uid='hop', password='123hop', dob=date(1906, 12, 9))
        users = [u1, u2, u3, u4]

        for user in users:
            try:
                for num in range(randrange(1, 4)):
                    note = "#### " + user.name + " note " + str(num) + ". \n Generated by test data."
                    user.posts.append(Post(id=user.id, note=note, image='ncs_logo.png'))
                user.create()
            except IntegrityError:
                db.session.remove()
                print(f"Records exist, duplicate email, or error: {user.uid}")

if __name__ == '__main__':
    app.run(debug=True)

            