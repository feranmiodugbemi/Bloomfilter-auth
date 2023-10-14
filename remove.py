from pybloom_live import ScalableBloomFilter
import os

def load_bloom_filter(filename):
    try:
        with open(f"bloom-filter/{filename}", 'rb') as f: 
            return ScalableBloomFilter.fromfile(f)
    except FileNotFoundError:
        return None

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

for feature in vehicle_features:
    filename = f"{feature}BF.blm"
    bloom_filter = load_bloom_filter(filename)
    if bloom_filter is not None:
        os.remove(f"bloom-filter/{filename}")  # Fixed the file removal path
