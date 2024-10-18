from flask import Flask, jsonify, request
from flask_marshmallow import Marshmallow
from marshmallow import fields, ValidationError, validate
from flask_sqlalchemy import SQLAlchemy
import mysql.connector
from mysql.connector import Error

my_db_password = input("Enter password for the database: ")
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+mysqlconnector://root:{my_db_password}@localhost/e_commerce_db'
db = SQLAlchemy(app)
ma = Marshmallow(app)

class Member(db.Model):
    __tablename__ = "Members"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    age = db.Column(db.Integer)
    sessions = db.relationship('WorkoutSession', backref='member') # Establishes the relationship with workout sessions

class MemberSchema(ma.Schema):
    '''Defining the Member Schema that takes an id, name, and age from the Fitness Center Database.'''
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1))
    age = fields.Int(required=True, validate=validate.Range(min=1))
    
    class Meta():
        fields = ("name", "age", "id")

class WorkoutSession(db.Model):
    __tablename__ = "WorkoutSessions"
    session_id = db.Column(db.Integer, primary_key=True)
    member_id = db.Column(db.Integer,db.ForeignKey("Members.id"))
    session_date = db.Column(db.Date, nullable=False)
    session_time = db.Column(db.String(50), nullable=False)
    activity = db.Column(db.String(255), nullable=False)

class WorkoutSessionSchema(ma.Schema):
    '''Defining the Workout Session Schema that takes a session id, member id, date, time, and activity from 
    the Fitness Center Database.'''
    session_id = fields.Integer(dump_only=True)
    member_id = fields.Integer(required=True, validate=validate.Range(min=1))
    session_date = fields.Date(required=True)
    session_time = fields.String(required=True, validate=validate.Length(min=1))
    activity = fields.String(required=True, validate=validate.Length(min=1))
    
    class Meta():
        fields = ("session_id", "member_id", "session_date", "session_time", "activity")

# Instantiating the schemas
member_schema = MemberSchema()
members_schema = MemberSchema(many=True)
workout_session_schema = WorkoutSessionSchema()
workout_sessions_schema = WorkoutSessionSchema(many=True)

# Initializing the database and creating the tables
with app.app_context(): 
    db.create_all()

# -------------------------------------------------------------------- #
# ADD MEMBER
@app.route("/members", methods=["POST"])
def add_member():
    try: 
        member_data = member_schema.load(request.json) # Retrieve member from user
    except ValidationError as e: # Handle validation error
        print(f"Error: {e}")
        return jsonify(e.messages), 400
    new_member = Member(name = member_data["name"], age = member_data["age"]) # Create new member
    db.session.add(new_member) # Add new member to the database
    db.session.commit() # Commit
    return jsonify({"message": "New member added successfully!"}), 201 # Return success

# -------------------------------------------------------------------- #
# UPDATE MEMBER
@app.route("/member/<int:id>", methods=["PUT"])
def update_member(id):
    member = Member.query.get(id) # Check if the member is in the database
    if not isinstance(member, Member): # Handle if member is not found
        return jsonify({"error":"Member not found"}), 404
    try: 
        member_data = member_schema.load(request.json) # Receive member data from user
    except ValidationError as e: # Handle validation errors
        print(f"Error: {e}")
        return jsonify(e.messages), 400
    # Update member's data
    member.name = member_data['name']
    member.age = member_data['age']
    db.session.commit() # Commit
    return jsonify({"message": "Member updated successfully!"}), 201 # Return success
    
# -------------------------------------------------------------------- #
# DELETE MEMBER
@app.route("/member/<int:id>", methods=["DELETE"])
def delete_member(id):
    member = Member.query.get(id) # Retrieve member by id
    # If member doesn't exist, inform user
    if not isinstance(member, Member):
        return jsonify({"error":"Member not found"}), 404
    db.session.delete(member) # Delete member
    db.session.commit() # Commit
    return jsonify({"message": "Member successfully removed!"}), 200 # Return success

# -------------------------------------------------------------------- #
# GET MEMBER BY NAME
@app.route("/search-members/by-name", methods=["GET"])
def search_members():
    name = request.args.get('name') # Retrieve member name to search for
    member = Member.query.filter_by(name=name).first() # Filter members for that name
    if member: # If member exists, return it
            return member_schema.jsonify(member)
    else: # Otherwise, inform user
        return jsonify({"error":"Member not found"}), 404

# -------------------------------------------------------------------- #
# GET ALL MEMBERS
@app.route("/members", methods=["GET"])
def get_members():
    members = Member.query.all() # Retrieve all members
    return members_schema.jsonify(members) # Return them

# -------------------------------------------------------------------- #
# ADD WORKOUT SESSION
@app.route("/workout-sessions", methods=["POST"])
def add_workout_session():
    try: 
        session_data = workout_session_schema.load(request.json) # Retrieve session from user
    except ValidationError as e: # Handle validation error
        print(f"Error: {e}")
        return jsonify(e.messages), 400
    member = Member.query.filter_by(id=session_data['member_id']).first()
    if member:
        # Create new session
        new_session = WorkoutSession(member_id = session_data["member_id"], session_date = session_data["session_date"], session_time=session_data['session_time'], activity=session_data['activity'])
        db.session.add(new_session) # Add new session to the database
        db.session.commit() # Commit
        return jsonify({"message": "New workout session added successfully!"}), 201 # Return success
    else:
        return jsonify({"error":"Member not found."}), 404
    
# -------------------------------------------------------------------- #
# UPDATE WORKOUT SESSION
@app.route("/workout-session/<int:session_id>", methods=["PUT"])
def update_workout_session(session_id):
    session = WorkoutSession.query.get(session_id) # Check if the member is in the database
    if not isinstance(session, WorkoutSession): # Handle if member is not found
        return jsonify({"error":"Workout session not found"}), 404
    try: 
        session_data = workout_session_schema.load(request.json) # Receive member data from user
    except ValidationError as e: # Handle validation errors
        print(f"Error: {e}")
        return jsonify(e.messages), 400
    member = Member.query.filter_by(id=session_data['member_id']).first()
    if member:
        # Update workout session's data
        session.member_id = session_data['member_id']
        session.session_date = session_data['session_date']
        session.session_time = session_data['session_time']
        session.activity = session_data['activity']
        db.session.commit() # Commit
        return jsonify({"message": "Workout session updated successfully!"}), 201 # Return success
    else:
        return jsonify({"error":"Member not found."}), 404
            
# -------------------------------------------------------------------- #
# DELETE WORKOUT SESSION
@app.route("/workout-session/<int:id>", methods=["DELETE"])
def delete_workout_session(id):
    # Retrieve workout session with that id
    session = WorkoutSession.query.get(id) 
    # Handle workout session not being found
    if not isinstance(session, WorkoutSession):
        return jsonify({"error":"Workout session not found"}), 404
    db.session.delete(session) # Delete workout session
    db.session.commit() # Commit
    return jsonify({"message": "Workout session successfully removed!"}), 200 # Return success
            
# -------------------------------------------------------------------- #
# GET WORKOUT SESSION BY SESSION ID
@app.route("/workout-session/<int:session_id>", methods=["GET"])
def get_workout_session(session_id):
    # Retrieve workout session with that id
    session = WorkoutSession.query.get(session_id)
    if session: # If it exists, return information
            return workout_session_schema.jsonify(session)
    else: # Otherwise, inform user
        return jsonify({"error":"Workout session not found"}), 404

# -------------------------------------------------------------------- #
# GET ALL WORKOUT SESSIONS
@app.route("/workout-sessions", methods=["GET"])
def get_workout_sessions():
    sessions = WorkoutSession.query.all() # Retrieve all workout sessions
    return workout_sessions_schema.jsonify(sessions)

# -------------------------------------------------------------------- #
# GET WORKOUT SESSIONS BY MEMBER NAME
@app.route("/workout-sessions/by-member", methods=["GET"])
def workout_session_by_member():
    name = request.args.get('member') # Retrieve member name from user
    member = Member.query.filter_by(name=name).first() # Find member, check if exists
    if member:
        member_id = member.id # Retrieve member id
        sessions = WorkoutSession.query.filter_by(member_id=member_id) # Filters workout sessions by member id
        if sessions:
                return workout_sessions_schema.jsonify(sessions) # Return work out sessions
        else:
            return jsonify({"error":"Workout session not found"}), 404 # Handle no workout sessions meeting criteria
    else:
        return jsonify({"error":"Member not found."}) # Handle no member found
            
if __name__ == "__main__":
    app.run(debug=True)