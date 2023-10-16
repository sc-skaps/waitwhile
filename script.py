
import json
import time
import requests
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
import os
import schedule
import hashlib
from datetime import datetime, timezone, timedelta
import pytz




def load_exported_ids(file_path):
    try:
        with open(file_path, 'r') as json_file:
            return json.load(json_file)
    except FileNotFoundError:
        return []
    

def save_exported_ids(file_path, exported_ids):
    with open(file_path, 'w') as json_file:
        json.dump(exported_ids, json_file)


def load_json(file_path):
    try:
        with open(file_path, 'r') as json_file:
            return json.load(json_file)
    except Exception as e:
        print(f"Error loading JSON file: {e}")
        return None
    



def convert_utc_to_est(utc_time_string):
    try:
        utc_timezone = pytz.timezone('UTC') # Create a UTC timezone object
        est_timezone = pytz.timezone('US/Eastern') # Create an Eastern Time (EST) timezone object

        utc_time = datetime.strptime(utc_time_string, "%Y-%m-%dT%H:%M:%S.%fZ") #The strptime method is used for parsing (converting) a string representation of a date and time into a datetime object in Python. It stands for "string parse time."

        # Set the UTC timezone for the parsed datetime object
        utc_time = utc_timezone.localize(utc_time)

        # Convert the UTC time to EST
        est_time = utc_time.astimezone(est_timezone)

        # Format the EST time as a string
        return est_time.strftime("%Y-%m-%d %H:%M:%S %Z")

    except ValueError:
        print(f"Error parsing UTC time: {utc_time_string}")
        return "N/A"


# Function to generate a hash for a record and save the timestamp
def generate_record_hash(record):


    # Convert the record into a JSON-formatted string with keys sorted
    record_string = json.dumps(record, sort_keys=True)

    # Compute an MD5 hash of the JSON-formatted string
    hash_value = hashlib.md5(record_string.encode()).hexdigest()

    # Get the current timestamp in a formatted string
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  

    # Return both the MD5 hash and the timestamp as strings
    return hash_value, timestamp  # Return both the hash and timestamp as strings


def create_pdf(data, ids, record_hashes): 
    try:
      
        styles = getSampleStyleSheet()
        style_normal = styles['Normal']
        style_bold = styles['Heading1']
        style_normal.fontSize = 15
        style_normal.leading = 16

        # the code starts iterating through each entry in the data list.
        for entry in data:


           
            id = entry['Id'] 
            record_hash, timestamp = generate_record_hash(entry)

            input_timestamp = entry['Date']


            
            if id in ids and record_hashes.get(str(id)) and record_hashes[str(id)][0] == record_hash:
                print(f"Record with ID {id} already exported. Skipping.")
                continue

            # this field is for the PDF name and Folder name
            first_name = entry['First Name']
            phone_number = entry['Phone']
            current_date = datetime.now()
            year_folder_name = f"Shipping {current_date.year}"
            month_folder_name = current_date.strftime('%B')  # Month name
            day_folder_name = current_date.strftime('%Y-%m-%d')

            # Create the directory structure if it doesn't exist
            year_folder_path = os.path.join(base_directory, year_folder_name)
            month_folder_path = os.path.join(year_folder_path, month_folder_name)
            day_folder_path = os.path.join(month_folder_path, day_folder_name)

            os.makedirs(day_folder_path, exist_ok=True)

            # This line defines the PDF file name based on the extracted data.
            pdf_name = os.path.join(day_folder_path, f'{id}_{first_name}_{phone_number}.pdf')

            # This line creates a SimpleDocTemplate object for the PDF document 
            # using the specified file name and page size (A4).
            doc = SimpleDocTemplate(pdf_name, pagesize=A4)

            page_width, page_height = A4
            margin = 40
            logo_height = 100
            available_space = page_width - 2 * margin
            first_row_widths = [available_space * 0.5, available_space * 0.5]
            other_rows_widths = [available_space * 0.9, available_space * 0.1]

            # This line defines an inner function create_content_block that takes data as its argument. 
            # This function will be used to create the content of the PDF document.
            def create_content_block(data):

                # This line initializes an empty list called content to store the content of the PDF.
                content = []
                    
                # This block defines data for the first row of the PDF content, 
                # including an image (logo) and a bold title.
                first_row_data = [
                    [Image('skaps_logo.png', width=100, height=logo_height), Paragraph("<b>SKAPS INDUSTRIES</b>", ParagraphStyle(name='SKAPS', fontSize=24, alignment=1))],
                ]


                # This line creates a table using the data defined in first_row_data 
                # and sets the column widths.
                first_row_table = Table(first_row_data, colWidths=first_row_widths)
                # first_row_table.setStyle(TableStyle([('ALIGN', (0, 0), (-1, -1), 'CENTER'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))

                # This block sets styles for the first row table, including alignment and vertical alignment.
                first_row_table.setStyle(TableStyle([('ALIGN', (0, 0), (0, 1), 'LEFT'),  # Align the logo to the left
                ('ALIGN', (1, 0), (1, 1), 'RIGHT'),  # Align the text to the right
                ('VALIGN', (0, 0), (1, 1), 'MIDDLE'),  # Vertically center both cells
                ]))

                # These lines add the first row table and a spacer (vertical space) to the content list.
                content.append(first_row_table)
                content.append(Spacer(1, 20))


                # This block defines data for other rows of the PDF content.
                # It includes various fields and their values from the entry data.
                other_rows_data = [
                    [''],
                    [''],
                    [Paragraph(f"<b> DRIVER SIGN IN FORM </b>", style_bold), ''],
                    [Paragraph(f"Id: <b>{data['Id']}</b>", style_normal), ''],
                    # [Paragraph(f"Driver Name: <b>{data['First Name']}</b>", style_normal), ''],
                    # [Paragraph(f"Driver Name: <b>{data['Last Name']}</b>", style_normal), ''],
                    [Paragraph(f"Driver Name: <b>{data['First Name']} {data['Last Name']}</b>", style_normal), ''],
                    [Paragraph(f"Date: <b>{convert_utc_to_est(input_timestamp)}</b>", style_normal), ''],
                    [Paragraph(f"Phone: <b>{data['Phone']}</b>", style_normal), ''],
                    [Paragraph(f"Carrier: <b>{data['Carrier']}</b>", style_normal), ''],
                    [Paragraph(f"Broker: <b>{data['Broker']}</b>", style_normal), ''],
                    [Paragraph(f"Customer PO #: <b>{data['Customer PO #']}</b>", style_normal), ''],
                    [Paragraph(f"Destination: <b>{data['Destination']}</b>", style_normal), ''],
                    [Paragraph(f"Trailer/Container Number: <b>{data['Trailer/Container Number']}</b>", style_normal), ''],
                    [Paragraph(f"Vehicle Type: <b>{data['Vehicle Type']}</b>", style_normal), ''],
                    [Paragraph(f"Scheduled Appointment Time: <b> {data['Scheduled Appointment Time']}</b>", style_normal), ''],
                    [Paragraph(f"Dispatcher Name: <b>{data['Dispatcher Name']}</b>", style_normal), ''],
                    [Paragraph(f"Dispatcher Phone: <b>{data['Dispatcher Phone']}</b>", style_normal), ''],
                    [Paragraph(f"Customer Name: <b>{data['Customer Name']}</b>", style_normal), ''],
                    [Paragraph(f"Scanner: <b>{data['Scanner']}</b>", style_normal), ''],
                    [Paragraph(f"Loader:_______________________", style_normal), ''],
                    [Paragraph(f"Dock In Time: <b>{data['Dock In Time']}</b>", style_normal), ''],
                    [Paragraph(f"Dock Out Time: <b>{data['Dock Out Time']}</b>", style_normal), ''],
                    [Paragraph(f"Timbers Used: <b>{data['Timbers Used']}</b>", style_normal), ''],
                    [Paragraph(f"Poles Used: <b>{data['Poles Used']}</b>", style_normal), ''],
                    [Paragraph(f"Truck Assigned by:________________________", style_normal), '']
                ]

                # This block creates a table for other rows of data and 
                # sets styles for alignment and vertical alignment.
                other_rows_table = Table(other_rows_data, colWidths=other_rows_widths)
                other_rows_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))

                # These lines add the other rows table and a spacer to the content list.
                content.append(other_rows_table)
                content.append(Spacer(1, 20))
                
                # This line returns the content list containing the PDF content.
                return content

            content_list = []

            # This line calls the create_content_block function 
            # to create the content for the PDF based on the current entry.
            content_list = create_content_block(entry)

            # This line builds the PDF document using the content list.
            doc.build(content_list)
            # This line prints a message indicating the location where the PDF has been saved.
            print(f'PDF saved at {pdf_name}')

            # These lines update the ids list with the current ID, save the updated ids 
            # to a JSON file, and update the record_hashes with the current record's 
            # hash and timestamp.
            ids.append(id)
            save_exported_ids('exported_ids.json', ids)
            record_hashes[str(id)] = (record_hash, timestamp)

    # This block catches and handles any exceptions that 
    # may occur during PDF creation and prints an error message.
    except Exception as e:
        print(f"Error creating PDF: {e}")


def fetch_and_process_waitwhile_data():

    url = "https://api.waitwhile.com/v2/visits/export?format=JSON&fromTime=2023-09-24T08%3A46%3A00%2B0000&dateRangeField=created"
    headers = {"apikey": "jYHW6jItb9fQxUD57YHSIn7b"}


    response = requests.get(url, headers=headers)


    if response.status_code == 200:
        data_list = response.json()

    
        if isinstance(data_list, dict):
            data_list = [data_list]

    # This block of code writes the data_list to a JSON file named 'Data.json'.
        with open('Data.json', 'w') as f:
            json.dump(data_list, f)
        print("Data.json is successfully generated.")

    # These lines initialize a counter variable and create an empty list called new_data_list.
        counter = 1
        new_data_list = []

    # This line starts a for loop to iterate through the elements in data_list, and i is the index, 
    # data is the current data element being processed.
        for i,data in enumerate(data_list):
            print(f"Unique ID: {counter}")
            counter += 1

            # print(f"Fetched data {i + 1}:")


            fetched_data = {
                'Id': counter,
                'Date': data.get('created', 'N/A'),
                'First Name': data.get('firstName', 'N/A'),
                'Last Name': data.get('lastName', 'N/A'),
                'Phone': data.get('phone', 'N/A'),
                'Country': data.get('country', 'N/A'),
                'City': data.get('city', 'N/A'),
                'Carrier': get_first_element(data['fields'].get('tcY1X5Kb7h2uIWK53Lyg', [])),
                'Vehicle Type': get_first_element(data['fields'].get('i1I6xyqqxa6oTlE3DkYM', [])),
                'Trailer/Container Number': get_first_element(data['fields'].get('uMvYMV9AWZ1OGIbA1JKn', [])),
                'Destination': get_first_element(data['fields'].get('fikIvjiydrX5ofr6RvNi', [])),
                'Broker': get_first_element(data['fields'].get('NIzqc21iVthkg02MTLGG', [])),
                'Scheduled Appointment Time': get_first_element(data['fields'].get('7vccTLW6wx0uJTI8pTGV', [])),
                'Customer Name': get_first_element(data['fields'].get('60kWvZTF6SNkCEECXi66', [])),
                'Scanner': get_first_element(data['fields'].get('vGcgWk6xCnY3CjQuEgxa', [])),
                'Customer PO #': get_first_element(data['fields'].get('L325nfBjUROuGPa3qUJu', [])),
                'Dispatcher Name': get_first_element(data['fields'].get('w22E7B7dLi4SYeXxgzLG', [])),
                'Dispatcher Phone': get_first_element(data['fields'].get('ot2ggPrasvp776PDLArX', [])),
                'Dock In Time': get_first_element(data['fields'].get('8WHDY3nMaW2GlARauOn5', [''])),
                'Dock Out Time': get_first_element(data['fields'].get('BkDnZV8ZKyp8CH0oBacG', [])),
                'Poles Used': get_first_element(data['fields'].get('DAFP7BsGgqUest0w98tL', [])),
                'Timbers Used': get_first_element(data['fields'].get('RX6CchYy0g2NCGDu8wqx', [])),
            }

            # This line appends the fetched_data dictionary to the new_data_list.
            new_data_list.append(fetched_data)


            # This block of code prints each key-value pair in the fetched_data dictionary.
            for key, value in fetched_data.items():
                print(f"{key}: {value}")
            print()

        # This block of code writes the new_data_list to a JSON file named 'NewData.json'.
        with open('NewData.json', 'w') as f:
            json.dump(new_data_list, f)
        print("NewData.json is successfully generated.")

#------------------------------------------------------If we want to--------------------------------------
    
        # This line calls a function create_pdf and passes the new_data_list, exported_ids, 
        # and record_hashes as arguments.
        create_pdf(new_data_list, exported_ids, record_hashes)

        # Load the JSON data
        json_data = load_json('NewData.json')

        if json_data: #This line checks if json_data is not empty (i.e., if JSON data was successfully loaded).
            
            # These lines extract the 'Id' from the current entry and generate a record hash 
            # and timestamp using the generate_record_hash function.
            for entry in json_data:
                record_id = entry['Id']
                record_hash, timestamp = generate_record_hash(entry)

                # This line checks if the generated record_hash is different 
                # from the previously stored hash for the same record (if any).
                if record_hash != record_hashes.get(record_id, (None, 0))[0]: 

                    print(f'Record {record_id} is updated. Calling create_pdf function.')
                    # If the hash is different, it indicates that the record has been updated, 
                    # and this line prints a message and calls the create_pdf function.
                    create_pdf([entry], exported_ids, record_hashes)
                    
                    # These lines update the record_hashes dictionary with 
                    # the new hash and timestamp and save it to a file named 'record_hashes.json'.
                    record_hashes[record_id] = (record_hash, timestamp)
                    save_exported_ids('record_hashes.json', record_hashes)

                    # If the hash is the same as before, 
                    # this line prints a message indicating that the record is up-to-date.
                else:
                    print(f'Record {record_id} is up-to-date.')

        # If json_data is empty (indicating an error during JSON loading), this line prints an error message.
        else:
            print('Error fetching data from the API')

    # If the HTTP response status code is not 200 (indicating a failed request), 
    # this line prints an error message with the status code and response text.
    else:
        print(f"Failed to get data from Waitwhile API: {response.status_code}, {response.text}")

#------------------------------------------------------Get first element-----------------------------------

# Function to get the first element from a list or return a default value
# The get_first_element function you provided returns the first element of a given 
# list lst or a default value (a space ' ' by default) if the list is empty. 
# Here's an explanation of how it works:
def get_first_element(lst, default=' '):
    return lst[0] if len(lst) > 0 else default


#-------------------------------------------------------------------------------------------------------------


# Function to periodically clean up old record hashes
# The code you provided defines a function called cleanup_old_hashes that is 
# responsible for periodically cleaning up old entries in a record_hashes dictionary. 
# Here's a breakdown of what each part of the code does:

# The function starts by getting the current timestamp using datetime.now(). 
# It then calculates a timestamp that is 3 days ago using timedelta(days=3).

def cleanup_old_hashes(record_hashes):
    current_time = datetime.now()
    three_days_ago = current_time - timedelta(days=3)  # Calculate timestamp for 3 days ago

    # Iterate through the record_hashes dictionary and remove entries older than 3 days
    # The function iterates through the record_hashes dictionary. 
    # For each entry, it checks if the timestamp (parsed from the string) is older than the 
    # calculated three_days_ago timestamp. 
    # If it is, the record ID is added to the keys_to_remove list.
    keys_to_remove = []
    for record_id, (hash_value, timestamp) in record_hashes.items():
        if datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S") < three_days_ago:
            keys_to_remove.append(record_id)
    
    # After identifying the record IDs that need to be removed, 
    # the function then removes these old entries from the record_hashes dictionary 
    # using the del statement.
    
    # Remove the old entries
    for key in keys_to_remove:
        del record_hashes[key]

    # Save the updated record_hashes dictionary
    save_exported_ids('record_hashes.json', record_hashes)

#---------------Script will start and this is the first thing that would execute-------------------
    



# Define the base directory where the PDF folders will be created
base_directory = 'C:/Users/shashwat/Desktop/Updatedscript/export'  # Replace with your desired path


#-------------------------------------previously exported IDs and record hashes------------------------------------------------------------



# Load previously exported IDs and record hashes
# Load record hashes if the file exists, otherwise initialize as an empty dictionary
exported_ids = load_exported_ids('exported_ids.json')
try:
    record_hashes = load_json('record_hashes.json')
    if record_hashes is None:
        record_hashes = {}
except FileNotFoundError:
    record_hashes = {}


#-----------------------------------------------this will execute the script every minute---------------

# Schedule the script to run fetch_and_process_waitwhile_data every 1 minute
schedule.every(1).minutes.do(fetch_and_process_waitwhile_data)

#---------------------------------------------------------------------------------------------------------

#----------------------------------------------------Run the script Continuesly-----------------------------------

# Run the script continuously
while True:
    schedule.run_pending()
    cleanup_old_hashes(record_hashes)  # Clean up old hashes
    time.sleep(1)

#-----------------------------------------------------------------------------------------------------------------


