from email.mime.text import MIMEText
import smtplib
import pyotp
import random
import time
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
from pybloom_live import ScalableBloomFilter
import os
from dotenv import load_dotenv


print("Starting Bloomfilter Authentication system......")

# Define a function to load Bloom filters
def load_bloom_filter(filename):
    try:
        with open(f"bloom-filter/{filename}", 'rb') as f: 
            return ScalableBloomFilter.fromfile(f)
    except FileNotFoundError:
        return None

    

# Generate a TOTP secret and a TOTP instance
def generate_otp():
    totp_secret = pyotp.random_base32()
    totp = pyotp.TOTP(totp_secret)
    return totp.now()

def send_email(recipient_email, OTP):
    load_dotenv()
    sender_email = os.getenv("SENDER_EMAIL")
    sender_password = os.getenv("SENDER_PASSWORD")
    # Set up the SMTP server for Gmail
    smtp_server = 'smtp.gmail.com'
    port = 587

    # Create the email content
    msg = MIMEText(f"This is your OTP(One time password), please don't share with anyone: {OTP}")
    msg['Subject'] = "OTP for Bloom-auth"
    msg['From'] = sender_email
    msg['To'] = recipient_email

    try:
        # Connect to the SMTP server
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()
        server.login(sender_email, sender_password)

        # Send the email
        server.sendmail(sender_email, recipient_email, msg.as_string())

        # Close the server connection
        server.quit()

        print('Email sent successfully.')
    except Exception as e:
        print(f"Error: {e}")
        return False

expiration_time = datetime.now() + timedelta(minutes=5)


# get the current date and time
now = datetime.now()


# Choose a random number r and the current timestamp t
r = random.randint(1, 1000)
t = int(time.time())
# Use r and t as the seed to randomly permute a set of numbers, choosing the first number as the vehicle feature threshold fi to be considered
seed = random.seed(str(r) + str(now))
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
        authentication_passed = False
        print(f"{feature} Bloom filter does not exist.")

# Print final result
if authentication_passed:
    print("Authentication passed.")
    username = input("Input your email: ")
    user_email = input("Input your email: ")
    otp = generate_otp()
    email_sent = send_email(user_email, otp)
    submitted_otp = input('Enter OTP: ')
    # Store the OTP and expiration time in a database or a secure storage
    # For simplicity, we'll use a dictionary as a simple in-memory storage
    otp_data = {'otp': otp, 'expiration_time': expiration_time}
    if submitted_otp == otp_data['otp'] and datetime.now() < otp_data['expiration_time']:
        print('OTP is valid.')
        print("Authentication successful")
    else:
        print('OTP is invalid or expired.')
    
    
else:
    print("Authentication failed.")
    option = input("Do you want to register (Yes/No): ").lower()
    if option == "no":
        print("Goodbye")
    elif option == "yes":
        new_user_input = {}
        for feature in vehicle_features:
            new_user_input[feature] = input(f"Input your {feature} detail: ")
        # Assuming 'new_user_input' contains the details for all vehicle features

        # Load the Bloom filters for selected features
        for feature in new_user_input.keys():
            filename = f"{feature}BF.blm"
            bloom_filter = ScalableBloomFilter()  # Create a new bloom filter
            bloom_filter.add(new_user_input[feature])  # Add the user input to the Bloom filter
            bloom_filter.tofile(open(f"bloom-filter/{filename}", 'wb'))  # Save the bloom filter
            print("Vehicle added successfully")
                
                