import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
file_path = os.path.join(BASE_DIR, 'excel.txt')
# Define the file path


# Verify if the file exists
if not os.path.isfile(file_path):
    print(f"File not found at {file_path}")
else:
    # Read the file
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Initialize a dictionary to hold the parsed data
    data = {}

    # Process each line to normalize and parse it
    for line in lines:
        line = line.strip()
        if line.startswith("**"):
            line = line[2:].strip()
        elif line.startswith("-"):
            line = line[1:].strip()

        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()

            # Check if the key already exists in the dictionary
            if key not in data:
                data[key] = value
            else:
                # If the key exists, you can implement a rule to decide which value to keep
                # For example, prefer the value from the "**" line over the "-" line
                if line.startswith("**"):
                    data[key] = value

    print(data)
