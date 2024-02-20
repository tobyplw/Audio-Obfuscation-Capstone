from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import bcrypt
import certifi

#Connection String
uri = "mongodb+srv://allatt_audio:Capstone@capstone.v2sgpm7.mongodb.net/?retryWrites=true&w=majority"

#Connect to MongoDB
myclient = MongoClient(uri, tlsCAFile=certifi.where())

#Make sure connection works
try:
    myclient.admin.command('ping')
    print("You successfully connected to MongoDB!")
except Exception as e:
    print(e)


#Make new database
db = myclient["Capstone"]

#Make new collections called 'Users' and 'Calls'
Users = db["Users"]
Calls = db["Calls"]

#Function to create a new user
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

#Function to login a current user
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

#Function to update a users ip
def update_ip (username, ip_address):
    current_user = {"username": username}
    updated_user = { "$set": { "ip_address": ip_address } }
    update_doc = Users.update_one(current_user,updated_user)

#Function to log a users call
def log_call (caller, callee, call_date, call_duration, call_transcript):
    new_call = {"caller": caller, 
                "callee": callee, 
                "call_date": call_date, 
                "call_duration": call_duration, 
                "call_transcript": call_transcript
                }
    Calls.insert_one(new_call)



