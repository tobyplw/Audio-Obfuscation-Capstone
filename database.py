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

def add_input_device(username, input_device):
    # Update the document with the user's input device preference
    user_update_result = Users.update_one(
        {"username": username},
        {"$set": {"input_device": input_device}},
        upsert=True
    )
    # Check if the operation was successful
    if user_update_result.matched_count > 0:
        print(f"Updated input device for user: {username}")
    elif user_update_result.upserted_id is not None:
        print(f"Created input device preference for new user: {username}")
    else:
        print("No changes made to the database.")

def add_output_device(username, output_device):
    # Update the document with the user's output device preference
    user_update_result = Users.update_one(
        {"username": username},
        {"$set": {"output_device": output_device}},
        upsert=True
    )
    # Check if the operation was successful
    if user_update_result.matched_count > 0:
        print(f"Updated output device for user: {username}")
    elif user_update_result.upserted_id is not None:
        print(f"Created output device preference for new user: {username}")
    else:
        print("No changes made to the database.")


def add_contact(username, contact_username, contact_nickname):
    # Fetch the user's document to update
    user = Users.find_one({"username": username})

    if user:
        # Check if "contacts" field exists, if not create it as an empty list
        if "contacts" not in user:
            user["contacts"] = []
        
        # Append the new contact to the user's contacts list
        # Ensuring no duplicate contact is added
        if not any(contact['username'] == contact_username for contact in user["contacts"]):
            user["contacts"].append({"username": contact_username, "nickname": contact_nickname})
        
            # Update the user document with the new contacts list
            update_result = Users.update_one({"username": username}, {"$set": {"contacts": user["contacts"]}})
            
            if update_result.modified_count > 0:
                print(f"Contact {contact_username} added to {username}'s contacts.")
            else:
                print("No changes made to the database.")
        else:
            print("Contact already exists.")
    else:
        print("User not found.")

