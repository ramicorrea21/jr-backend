from flask import jsonify, request
from app import app 
from models import db, Users, Profile, Services, Requests
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from sqlalchemy.exc import IntegrityError

#populate db
user_path = os.path.join(os.path.dirname(__file__), "users.json")
profiles_path = os.path.join(os.path.dirname(__file__), "profiles.json")
services_path = os.path.join(os.path.dirname(__file__), "services.json")
requests_path = os.path.join(os.path.dirname(__file__), "requests.json")

@app.route("/user-population", methods=["GET"])
def user_population():
    with open(user_path, "r") as file:
        data = json.load(file)
        file.close
        
        for user in data:
            user = Users(
                user_handle=user['user_handle'],
                user_email=user['user_email'],
                password = user['password']
            )
            db.session.add(user)
        try:
            db.session.commit()
            return jsonify({"message":"users populated"})
        except Exception as error:
            db.session.rollback()
            return jsonify({"error":f"{error.args}"})

@app.route("/profiles-population", methods=["GET"])
def profiles_population():
    with open(profiles_path, "r") as file:
        data = json.load(file)
        file.close

    for profile in data:
        profile = Profile(
            user_id=profile['user_id'],
            first_name = profile['first_name'],
            last_name = profile['last_name'],
            description = profile['description'],
            phone = profile['phone'],
            location = profile['location'],
            address = profile['address'],
            profession = profile['profession'],
            category = profile['category']
        )
        db.session.add(profile)

    try:
        db.session.commit()
        return jsonify({"message":"profiles populated"})
    except Exception as error:
        db.session.rollback()
        return jsonify({"error":f"{error.args}"})

@app.route('/services-population', methods=["GET"])
def services_population():
    with open(services_path, "r") as file:
        data = json.load(file)
        file.close
    
    for service in data:
        service = Services(
            user_id = service['user_id'],
            title = service['title'],
            description = service['description'],
            category = service['category'],
            is_remote = service['is_remote'],
            location = service['location'],
            price_range = service['price_range']
        )
        db.session.add(service)
    try:
        db.session.commit()
        return jsonify({"message":"services populated"})
    except Exception as error:
        db.session.rollback()
        return jsonify({"error":f"{error.args}"})
    
@app.route('/requests-population', methods=["GET"])
def requests_population():
    with open(requests_path, "r") as file:
        data = json.load(file)
        file.close
    
    for request in data:
        request = Requests(
            user_id = request['user_id'],
            title = request['title'],
            description = request['description'],
            category = request['category'],
            is_remote = request['is_remote'],
            location = request['location'],
            price_range = request['price_range']
        )
        db.session.add(request)
    try:
        db.session.commit()
        return jsonify({"message":"requests populated"})
    except Exception as error:
        db.session.rollback()
        return jsonify({"error":f"{error.args}"})

#post user
#password security:
def set_password(password):
    return generate_password_hash(f"{password}")

def check_password(hash_password, password):
    return check_password_hash(hash_password, f"{password}")

#endpoint
@app.route('/post_user', methods=['POST'])
def post_user():
    data = request.json
    user_handle = data.get('user_handle')
    user_email = data.get('user_email')
    password = data.get('password')

    #validating if the user already exists
    if user_handle is None or user_email is None or password is None:
        return jsonify({"error":"bad request"}), 400
    
    handle = Users.query.filter_by(user_handle=user_handle).one_or_none()
    email = Users.query.filter_by(user_email = user_email). one_or_none()

    if handle is not None:
        return jsonify({"message":"username already exists"}), 400
    if email is not None:
        return jsonify({"message":"email already exists"}), 400
    
    #creating new user
    password = set_password(password)
    new_user = Users(
        user_handle = user_handle,
        user_email = user_email, 
        password = password
    )
    db.session.add(new_user)
    try:
        db.session.commit()
        return jsonify({"message": "user added correctly"}), 201
    except Exception as error:
        db.session.rollback()
        return jsonify({"error": f"{error.args}"}), 500
    

#logintoken
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        user_email = data.get('user_email')
        password = data.get('password')

        #validate if the credentials are good
        user = Users.query.filter_by(user_email = user_email).one_or_none()
        if user is None or not check_password_hash(user.password, f'{password}'):
            return jsonify({'message': 'Invalid email or password'}), 400
    
        #if the credentials match, generate a login token
        token = create_access_token(
            identity={
                'email' : user.user_email,
                'id' : user.id
            }
        )
        return jsonify({'token': f"{token}"}), 200
    
    except Exception as error:
        return jsonify({"error":f"{error}"}), 500
    

#fetch user
    
@app.route('/fetch_user', methods=['GET'])
@jwt_required()
def fetch_user():
    user_id = get_jwt_identity()["id"]  
    user_data = Users.query.filter_by(id=user_id).one_or_none()
    profile_data = Profile.query.filter_by(user_id=user_id).one_or_none()

    if not user_data:
        return jsonify({"error": "User not found"}), 404

    user_serialized = user_data.serialize()
    profile_serialized = profile_data.serialize() if profile_data else None

    return jsonify({
        "user": user_serialized,
        "profile": profile_serialized
    }), 200


#post profile

@app.route('/post-profile', methods=['POST'])
@jwt_required()
def post_profile():
    user_id = get_jwt_identity()["id"]
    data = request.json
    profile_exists = Profile.query.filter_by(user_id=user_id).one_or_none()

    if profile_exists:
        return jsonify({"error": "Profile already exists"}), 400

    try:
        new_profile = Profile(
            user_id=user_id,
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            description=data.get('description'),
            phone=data.get('phone'),
            country=data.get('country'),
            city=data.get('city'),
            province=data.get('province'),
            address=data.get('address'),
            profession=data.get('profession'),
            category=data.get('category')
        )
        db.session.add(new_profile)
        db.session.commit()


        return jsonify(new_profile.serialize()), 201

    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"error": "Data integrity issue"}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

#update profile

@app.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = get_jwt_identity()['id']
    data = request.json
    profile_to_update = Profile.query.filter_by(user_id=user_id).first()

    if not profile_to_update:
        return jsonify({"error": "Profile not found"}), 404

    # Actualización condicional de campos
    for field in ['first_name', 'last_name', 'description', 'phone', 'city', 'country', 'province' 'address', 'profession', 'category']:
        if field in data:
            setattr(profile_to_update, field, data[field])

    try:
        db.session.commit()
        return jsonify(profile_to_update.serialize()), 200
    except Exception as error:
        db.session.rollback()
        return jsonify({"error": str(error)}), 500
#post service
#edit service
#delete service
#post request
#edit request
#delete request    





