from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_mongoengine import MongoEngine
from pymongo import MongoClient
from datetime import datetime as dt
import datetime


client = MongoClient("mongodb://localhost:27017/") # your connection string
db = client["demo"]
users_collection = db["users"]

app = Flask(__name__)
app.config["MONGODB_SETTINGS"] = {
    "host": "mongodb://localhost:27017/mydb"
}

db = MongoEngine(app)
jwt = JWTManager(app)
app.config['JWT_SECRET_KEY'] = 'Your_Secret_Key'
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=1)

# Make the WSGI interface available at the top level so wfastcgi can get it.
wsgi_app = app.wsgi_app

class new_user(db.Document):
    email = db.StringField(required=True, unique=True)
    password = db.StringField(required=True, min_length=6)
    created = db.DateTimeField(required=True, default=dt.now())
    updated = db.DateTimeField(required=True, default=dt.now())

class new_profile(db.Document):
    id_user = db.StringField(required=True)
    name = db.StringField()
    surname = db.StringField()
    phone = db.StringField()
    created = db.DateTimeField(required=True, default=dt.now())
    updated = db.DateTimeField(required=True, default=dt.now())

# Routes
@app.route("/register", methods=["POST"])
def register():
    email = request.json["email"]
    password = request.json["password"]
    user = new_user(email=email, password=password)
    user.save()
    return jsonify({"message": "User created successfully"})

@app.route("/login", methods=["POST"])
def login():
    email = request.json["email"]
    password = request.json["password"]
    user = new_user.objects(email=email, password=password).first()
    if user:
        access_token = create_access_token(identity=user.email)
        return jsonify({"access_token": access_token})
    else:
        return jsonify({"message": "Invalid email or password"})

@app.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    email = get_jwt_identity()
    user = new_user.objects(email=email).first()
    profile = new_profile.objects(id_user=str(user.id)).first()
    return jsonify(profile.to_json())

@app.route("/create_profile", methods=["POST"])
@jwt_required()
def create_profile():
    email = get_jwt_identity()
    user = new_user.objects(email=email).first()
    name = request.json["name"]
    surname = request.json["surname"]
    phone = request.json["phone"]
    profile = new_profile(id_user=str(user.id), name=name, surname=surname, phone=phone)
    profile.save()
    return jsonify({"message": "Profile created successfully"})

@app.route("/update_profile", methods=["PUT"])
@jwt_required()
def update_profile():
    current_user = get_jwt_identity() # Get the identity of the current user
    user_from_db = users_collection.find_one({'username' : current_user})
    if user_from_db:
        del user_from_db['_id'], user_from_db['password'] # delete data we don't want to return
        return jsonify({'profile' : user_from_db }), 200
    else:
        return jsonify({'msg': 'Profile not found'}), 404


if __name__ == '__main__':
    app.run(port =5003, debug=True)