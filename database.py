from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import bcrypt
import certifi
import public_ip as ip
import socket
from datetime import date, datetime

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
def create_user (username, password):
    #Hash and salt password more security
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    created_at = datetime.now()

    
    new_user = {
        "username": username,
        "password": hashed_password, 
        "created_at": created_at,
        }
    Users.insert_one(new_user)


#Function to login a current user
def login(username, password):
    #Find user
    user = Users.find_one({"username": username})
    #Get users IP

    if user:
        # Login successful
        if bcrypt.checkpw(password.encode('utf-8'), user["password"]):
            return True 
        # Password does not match
        else:
            return False
    # Login Failed
    else:
        return False

#Function to log a users call
def log_call (caller, callee, call_date, call_duration, call_transcript):
    new_call = {"caller": caller, 
                "callee": callee, 
                "call_date": call_date, 
                "call_duration": call_duration, 
                "call_transcript": call_transcript
                }
    Calls.insert_one(new_call)



def get_calls(username):
    user = Users.find_one({"username": username})

    # Ensure you have the correct query to match the caller's ID with the stored calls
    calls_query = {
        "$or":[
            {"caller": user},
            {"callee": user}
        ]
    }

    calls = Calls.find(calls_query).sort("call_date")
    
    call_logs = []  # Initialize an empty list to store call log tuples

    # Iterate through the cursor returned by the find operation
    for call in calls:

        # Construct a tuple for each call
        call_log = (
            str(call["_id"]),  # Assuming each call has a unique ID stored under "_id"
            call["caller"]["username"],  # Caller's username
            call["callee"]["username"],  # Callee's username
            call["call_date"].strftime("%m-%d-%Y %H:%M:%S"),  # Formatting date, assuming it's stored as a datetime object
            call["call_transcript"]  # Assuming you store the transcript directly
        )
        call_logs.append(call_log)  # Add the tuple to the list

    return call_logs

