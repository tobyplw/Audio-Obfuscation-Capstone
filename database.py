import pymongo
import bcrypt

myclient = pymongo.MongoClient("mongodb://localhost:27017")

db = myclient["Capstone"]

Users = db["Users"]
Calls = db["Calls"]

def create_user (username, password, created_at, ip_address):
    #Hash and salt password more security
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    new_user = {
        "username": username,
        "password": hashed_password, 
        "created_at": created_at, 
        "ip_address":ip_address
        }
    Users.insert_one(new_user)

def login(username, password):
    user = Users.find_one({"username": username})
    
    if user:
        if bcrypt.checkpw(password.encode('utf-8'), user["password"]):
            # Login successful
            return True 
        else:
            # Password does not match
            return False  # Password does not match
    else:
        return False

def update_ip (username, ip_address):
    current_user = {"username": username}
    updated_user = { "$set": { "ip_address": ip_address } }
    update_doc = Users.update_one(current_user,updated_user)

def log_call (caller, callee, call_date, call_duration, call_transcript):
    new_call = {"caller": caller, 
                "callee": callee, 
                "call_date": call_date, 
                "call_duration": call_duration, 
                "call_transcript": call_transcript
                }
    Calls.insert_one(new_call)
