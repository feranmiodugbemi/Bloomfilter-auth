import hashlib
import random
import time
from cryptography.fernet import Fernet
import datetime
import uuid
import signal
from pybloom_live import BloomFilter

print("Starting Bloomfilter Authentication system......")

# Define a function to load Bloom filters
def load_bloom_filter(filename):
    try:
        with open(filename, 'rb') as f:
            return BloomFilter.fromfile(f)
    except FileNotFoundError:
        return None
    

# get the current date and time
now = datetime.datetime.now()


# Choose a random number r and the current timestamp t
r = random.randint(1, 1000)
t = int(time.time())
print(t, r)
# Use r and t as the seed to randomly permute a set of numbers, choosing the first number as the vehicle feature threshold fi to be considered
seed = random.seed(str(r) + str(now))
print(seed)
vehicle_features = [
    "Vehicle_Registration_Number",
    "Vehicle_Identification_Number",
    "License_Plate_Number",
    "Engine_Serial_Number",
    "Tire_Size",
    "Vehicle_Class",
    "Transmission_Serial_Number",
    "Vehicle_Weight",
    "Axle_Ratio",
    "Vehicle_Odometer_Reading"
]

random.shuffle(vehicle_features)
fi = random.randint(2, len(vehicle_features))

# Of all available secret vehicle features, fi number of features will be randomly selected
selected_features = vehicle_features[:fi]

# Create input for selected features
user_input = {}
for feature in selected_features:
    user_input[feature] = input(f"Input your {feature} detail: ")

# Check all inputs against their respective Bloom filters
authentication_passed = True

for feature, choice in user_input.items():
    filename = f"{feature}BF.blm"
    bloom_filter = load_bloom_filter(filename)
    
    if bloom_filter is not None:
        if choice not in bloom_filter:
            authentication_passed = False
            print(f"Authentication failed for {feature}.")
    else:
        print(f"{feature} Bloom filter does not exist.")

# Print final result
if authentication_passed:
    print("Authentication passed.")
else:
    print("Authentication failed.")
    option = input("Do you want to register (Yes/No): ").lower()
    if option == "no":
        print("Goodbye")
    elif option == "yes":
        new_user_input = {}
        for feature in vehicle_features:
            new_user_input[feature] = input(f"Input your {feature} detail: ")

        # Define a function to load Bloom filters
        def load_bloom_filter(filename):
            try:
                with open(filename, 'rb') as f:
                    return BloomFilter.fromfile(f)
            except FileNotFoundError:
                return None

        # Assuming 'new_user_input' contains the details for all vehicle features

        # Load the Bloom filters for selected features
        for feature in new_user_input.keys():
            filename = f"{feature}BF.blm"
            bloom_filter = load_bloom_filter(filename)

            if bloom_filter is not None:

                # Add the user input to the Bloom filter
                bloom_filter.add(new_user_input[feature])
                print("Vehicle added successfully")

            else:
                print(f"{feature} Bloom filter does not exist.")

        
        
