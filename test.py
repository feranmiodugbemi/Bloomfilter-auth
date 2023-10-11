from pybloom_live import BloomFilter

Vehicle_Registration_NumberBF = BloomFilter(capacity=10000, error_rate=0.001)
Vehicle_Identification_NumberBF = BloomFilter(capacity=10000, error_rate=0.001)
License_Plate_NumberBF = BloomFilter(capacity=10000, error_rate=0.001)
Engine_Serial_NumberBF = BloomFilter(capacity=10000, error_rate=0.001)
Tire_SizeBF = BloomFilter(capacity=10000, error_rate=0.001)
Vehicle_ClassBF = BloomFilter(capacity=10000, error_rate=0.001)
Transmission_Serial_NumberBF = BloomFilter(capacity=10000, error_rate=0.001)
Vehicle_WeightBF = BloomFilter(capacity=10000, error_rate=0.001)
Axle_RatioBF = BloomFilter(capacity=10000, error_rate=0.001)
Vehicle_Odometer_ReadingBF = BloomFilter(capacity=10000, error_rate=0.001)

# Define your cars
car1 = {
    "Vehicle_Registration_Number": "AB123CD",
    "Vehicle_Identification_Number": "1HGCM82633A123456",
    "License_Plate_Number": "XYZ789",
    "Engine_Serial_Number": "E12345",
    "Tire_Size": "P215/60R16",
    "Vehicle_Class": "sedan",
    "Transmission_Serial_Number": "T1234",
    "Vehicle_Weight": "3500 lbs",
    "Axle_Ratio": "3.42",
    "Vehicle_Odometer_Reading": "65000 miles"
}


car2 = {
    "Vehicle_Registration_Number": "EF456GH",
    "Vehicle_Identification_Number": "2T2BK1BA6DC123456",
    "License_Plate_Number": "ABC123",
    "Engine_Serial_Number": "F54321",
    "Tire_Size": "P225/65R17",
    "Vehicle_Class": "SUV",
    "Transmission_Serial_Number": "T5678",
    "Vehicle_Weight": "4200 lbs",
    "Axle_Ratio": "3.73",
    "Vehicle_Odometer_Reading": "45000 miles"
}

car3 = {
    "Vehicle_Registration_Number": "GH789IJ",
    "Vehicle_Identification_Number": "1FTFW1EF0BFA12345",
    "License_Plate_Number": "DEF456",
    "Engine_Serial_Number": "S67890",
    "Tire_Size": "LT265/70R17",
    "Vehicle_Class": "truck",
    "Transmission_Serial_Number": "T9012",
    "Vehicle_Weight": "6000 lbs",
    "Axle_Ratio": "4.10",
    "Vehicle_Odometer_Reading": "80000 miles"
}


# Insert data into Bloom filters
for car in [car1, car2, car3]:
    Vehicle_Registration_NumberBF.add(car["Vehicle_Registration_Number"])
    Vehicle_Identification_NumberBF.add(car["Vehicle_Identification_Number"])
    License_Plate_NumberBF.add(car["License_Plate_Number"])
    Engine_Serial_NumberBF.add(car["Engine_Serial_Number"])
    Tire_SizeBF.add(car["Tire_Size"])
    Vehicle_ClassBF.add(car["Vehicle_Class"])
    Transmission_Serial_NumberBF.add(car["Transmission_Serial_Number"])
    Vehicle_WeightBF.add(car["Vehicle_Weight"])
    Axle_RatioBF.add(car["Axle_Ratio"])
    Vehicle_Odometer_ReadingBF.add(car["Vehicle_Odometer_Reading"])


# Save Bloom filters to .blm files
Vehicle_Registration_NumberBF.tofile(open('Vehicle_Registration_NumberBF.blm', 'wb'))
Vehicle_Identification_NumberBF.tofile(open('Vehicle_Identification_NumberBF.blm', 'wb'))
License_Plate_NumberBF.tofile(open('License_Plate_NumberBF.blm', 'wb'))
Engine_Serial_NumberBF.tofile(open('Engine_Serial_NumberBF.blm', 'wb'))
Tire_SizeBF.tofile(open('Tire_SizeBF.blm', 'wb'))
Vehicle_ClassBF.tofile(open('Vehicle_ClassBF.blm', 'wb'))
Transmission_Serial_NumberBF.tofile(open('Transmission_Serial_NumberBF.blm', 'wb'))
Vehicle_WeightBF.tofile(open('Vehicle_WeightBF.blm', 'wb'))
Axle_RatioBF.tofile(open('Axle_RatioBF.blm', 'wb'))
Vehicle_Odometer_ReadingBF.tofile(open('Vehicle_Odometer_ReadingBF.blm', 'wb'))