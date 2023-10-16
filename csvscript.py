import csv
import os
import pytz
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Image, Paragraph, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.units import inch
import requests
import schedule
import time
from urllib.parse import quote

# Define the CSV file to store generated data
data_store_file_csv = 'generated_data.csv'
api_key_file_path = 'apikey.txt'

# Function to create the CSV file if it doesn't exist
def create_csv_file():
    if not os.path.exists(data_store_file_csv):
        with open(data_store_file_csv, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Record ID', 'Timestamp'])

# Function to load generated data from CSV file
def load_generated_data_csv():
    data = {}
    try:
        with open(data_store_file_csv, 'r', newline='') as file:
            reader = csv.reader(file)
            next(reader)  # Skip the header row
            for row in reader:
                data[row[0]] = row[1]
    except FileNotFoundError:
        pass
    return data

# Function to save generated data to CSV file
def save_generated_data_csv(data):
    create_csv_file()
    existing_data = load_generated_data_csv()  # Load existing data from the CSV file

    try:
        with open(data_store_file_csv, 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['Record ID', 'Last Updated Time'])  # Write the header row
            for record_id, timestamp in data.items():
                writer.writerow([record_id, timestamp])
        print(f"Data saved to {data_store_file_csv}")
    except Exception as e:
        print(f"Error saving data to CSV file: {e}")
        
# Function to delete the CSV file daily at 6:10 AM
def delete_csv_file_daily():
    current_time = datetime.now(pytz.timezone('US/Eastern'))
    if current_time.hour == 6 and current_time.minute == 10:
        delete_csv_file()

# Function to delete the CSV file
def delete_csv_file():
    try:
        os.remove(data_store_file_csv)
        print(f"{data_store_file_csv} deleted.")
    except FileNotFoundError:
        print(f"{data_store_file_csv} not found.")
    except Exception as e:
        print(f"Error deleting {data_store_file_csv}: {e}")

# Function to generate the dynamic URL
def generate_dynamic_url():
    current_time = datetime.now()

    # Calculate the starting time (today at 6:00 AM)
    start_time = current_time.replace(hour=6, minute=0, second=0, microsecond=0)

    # Calculate the ending time (tomorrow at 6:00 AM)
    end_time = start_time + timedelta(days=1)

    # Format the dates in the desired format and properly encode them
    from_time = quote(start_time.strftime("%Y-%m-%dT%H:%M:%S+0000"))
    to_time = quote(end_time.strftime("%Y-%m-%dT%H:%M:%S+0000"))

    # Construct the URL
    base_url = "https://api.waitwhile.com/v2/visits/export"
    params = {
        "format": "JSON",
        "fromTime": from_time,
        "toTime": to_time,
        "dateRangeField": "created"
    }
    url = f"{base_url}?{'&'.join([f'{key}={value}' for key, value in params.items()])}"
    print(url)

    return url

# Function to convert UTC time to Eastern Time (EST)
def convert_utc_to_est(utc_time_string):
    if utc_time_string == 'N/A':
        return 'N/A'

    try:
        utc_timezone = pytz.timezone('UTC')
        est_timezone = pytz.timezone('US/Eastern')
        utc_time = datetime.strptime(utc_time_string, "%Y-%m-%dT%H:%M:%S.%fZ")
        utc_time = utc_timezone.localize(utc_time)
        est_time = utc_time.astimezone(est_timezone)
        return est_time.strftime("%Y-%m-%d %H:%M:%S %Z")
    except ValueError as e:
        print(f"Error parsing UTC time: {e}")
        return "N/A"

# Function to get the first element from a list or return 'N/A'
def get_first_element(lst):
    if lst:
        return lst[0]
    return '_______________________'

# Function to read API key from a text file
def read_api_key(api_key_file_path):
    try:
        with open(api_key_file_path, 'r') as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Error: The file '{api_key_file_path}' was not found.")
        return None

# Function to fetch data from the API
def fetch_data_from_api(url, api_key):
    try:
        headers = {"apikey": api_key}
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data_list = response.json()
            if isinstance(data_list, dict):
                data_list = [data_list]
            return data_list
        else:
            print(f"Failed to fetch data from the API. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error fetching data from the API: {e}")
    return []
# Function to create a PDF
def create_pdf(data_list):
    try:
        # Define styles for the content
        styles = getSampleStyleSheet()
        style_normal = styles['Normal']
        style_bold = styles['Heading1']
        style_normal.fontSize = 15
        style_normal.leading = 16

        # Define page layout parameters
        page_width, page_height = A4
        margin = 40
        logo_height = 100
        available_space = page_width - 2 * margin
        first_row_widths = [available_space * 0.5, available_space * 0.5]
        other_rows_widths = [available_space * 0.9, available_space * 0.1]

        # Create a directory to store PDF files
        exported_path='//multimedia/multimedia/SKAPS/Skaps2023/P-S'
        base_directory=exported_path
        current_date = datetime.now()
        year_folder_name = f"Shipping {current_date.year}"
        waitwhile_folder_name = "Waitwhile"
        month_folder_name = current_date.strftime('%B')  # Month name
        day_folder_name = current_date.strftime('%Y-%m-%d')
        year_folder_path = os.path.join(base_directory, year_folder_name)
        waitwhile_folder_path = os.path.join(year_folder_path, waitwhile_folder_name)
        month_folder_path = os.path.join(waitwhile_folder_path, month_folder_name)
        day_folder_path = os.path.join(month_folder_path, day_folder_name)
        os.makedirs(day_folder_path, exist_ok=True)



        # Load generated data from JSON file
        generated_data = load_generated_data_csv()

        # Iterate through data and create/update PDFs
        for counter, record in enumerate(data_list, start=1):
            created_value = record.get('created')
            if created_value is None:
                print(f"Skipping record ID {record.get('id')} due to missing 'created' field.")
                continue
            
            record_id = record.get('id', 'N/A')
            updated_ist = convert_utc_to_est(record.get('updated', 'N/A'))
            waitlist_time_ist = convert_utc_to_est(record.get('waitlistTime', 'N/A'))
            serve_time_ist = convert_utc_to_est(record.get('serveTime', 'N/A'))

            # Check if the record ID is already in the generated data
            if record_id in generated_data:
                # Check if the "updated" field has changed
                if generated_data[record_id] == updated_ist:
                    print(f"Skipping PDF generation for record ID {record_id}.")
                    continue  # Skip PDF generation
                        # Convert 'waitlistTime' and 'serveTime' to Eastern Time (EST)


            # Iterate through data and create PDFs
            fetched_data = {
                'Id': record.get('id', 'N/A'),
                'Date': convert_utc_to_est(record.get('created', 'N/A')),
                'First Name': record.get('firstName', 'N/A'),
                'Last Name': record.get('lastName', 'N/A'),
                'Phone': record.get('phone', 'N/A'),
                'Country': record.get('country', 'N/A'),
                'City': record.get('city', 'N/A'),
                'Carrier': get_first_element(record['fields'].get('tcY1X5Kb7h2uIWK53Lyg', [])),
                'Vehicle Type': get_first_element(record['fields'].get('i1I6xyqqxa6oTlE3DkYM', [])),
                'Trailer/Container Number': get_first_element(record['fields'].get('uMvYMV9AWZ1OGIbA1JKn', [])),
                'Destination': get_first_element(record['fields'].get('fikIvjiydrX5ofr6RvNi', [])),
                'Broker': get_first_element(record['fields'].get('NIzqc21iVthkg02MTLGG', [])),
                'Scheduled Appointment Time': get_first_element(record['fields'].get('7vccTLW6wx0uJTI8pTGV', [])),
                'Customer Name': get_first_element(record['fields'].get('60kWvZTF6SNkCEECXi66', [])),
                'Scanner': get_first_element(record['fields'].get('vGcgWk6xCnY3CjQuEgxa', [])),
                'Customer PO #': get_first_element(record['fields'].get('L325nfBjUROuGPa3qUJu', [])),
                'Dispatcher Name': get_first_element(record['fields'].get('w22E7B7dLi4SYeXxgzLG', [])),
                'Dispatcher Phone': get_first_element(record['fields'].get('ot2ggPrasvp776PDLArX', [])),
                'Dock In Time': get_first_element(record['fields'].get('8WHDY3nMaW2GlARauOn5', [])),
                'Dock Out Time': get_first_element(record['fields'].get('BkDnZV8ZKyp8CH0oBacG', [])),
                'Poles Used': get_first_element(record['fields'].get('DAFP7BsGgqUest0w98tL', [])),
                'Timbers Used': get_first_element(record['fields'].get('RX6CchYy0g2NCGDu8wqx', [])),
            }


            
            # Check if 'waitlistTime' is not 'N/A' and 'serveTime' is 'N/A'
            if (waitlist_time_ist != 'N/A' and serve_time_ist == 'N/A') or serve_time_ist != 'N/A':
                try:
                    # Define the PDF file path based on record information
                    pdf_file = os.path.join(day_folder_path, f"{fetched_data.get('First Name', 'N/A')}_{fetched_data.get('Last Name', 'N/A')}_{fetched_data.get('Phone', 'N/A')}.pdf")
                    # Create a SimpleDocTemplate for the PDF
                    doc = SimpleDocTemplate(pdf_file, pagesize=A4)
                    # Generate content for the PDF using the create_content_block function
                    content_list = create_content_block(fetched_data, style_normal, style_bold, available_space,
                                                        first_row_widths, other_rows_widths, logo_height)
                    # Build the PDF with the generated content
                    doc.build(content_list)
                    # Print a message indicating that the PDF has been saved
                    print(f'PDF saved at {pdf_file}')
                    # Update the generated_data dictionary with the current record's ID and timestamp
                    generated_data[record_id] = updated_ist
                    # Save the updated generated_data to the JSON file
                    save_generated_data_csv(generated_data)
                except PermissionError:
                    # If a PermissionError occurs, create a new PDF with an incremented name
                    pdf_file = None
                    counter_suffix = 1
                    while pdf_file is None or os.path.exists(pdf_file):
                        # Generate a new PDF file name with an incremented counter_suffix
                        pdf_file = os.path.join(day_folder_path, f"{fetched_data.get('First Name', 'N/A')}_{fetched_data.get('Last Name', 'N/A')}_{fetched_data.get('Phone', 'N/A')}_{counter_suffix}.pdf")
                        counter_suffix += 1

                    # Create a SimpleDocTemplate for the new PDF
                    doc = SimpleDocTemplate(pdf_file, pagesize=A4)
                    # Generate content for the PDF using the create_content_block function
                    content_list = create_content_block(fetched_data, style_normal, style_bold, available_space,
                                                        first_row_widths, other_rows_widths, logo_height)
                    # Build the new PDF with the generated content
                    doc.build(content_list)
                    # Print a message indicating that the new PDF has been saved
                    print(f'PDF saved at {pdf_file}')
                    # Update the generated_data dictionary with the current record's ID and timestamp
                    generated_data[record_id] = updated_ist
                    # Save the updated generated_data to the JSON file
                    save_generated_data_csv(generated_data)

    except Exception as e:
        print(f"Error creating PDF: {e}")

# Function to create content for the PDF
def create_content_block(data, style_normal, style_bold, available_space, first_row_widths, other_rows_widths, logo_height):
    content = []

    # Define data for the first row of the PDF content
    first_row_data = [
        [Image('skaps_logo.png', width=100, height=logo_height), Paragraph("<b>SKAPS INDUSTRIES</b>",
                                                                         style_bold)],
    ]

    # Create a table for the first row data and set styles
    first_row_table = Table(first_row_data, colWidths=first_row_widths)
    first_row_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (0, 1), 'LEFT'),
        ('ALIGN', (1, 0), (1, 1), 'RIGHT'),
        ('VALIGN', (0, 0), (1, 1), 'MIDDLE'),
    ]))

    # Add the first row table and a spacer to the content
    content.append(first_row_table)
    content.append(Spacer(1, 20))

    # Define data for other rows of the PDF content
    # Define data for other rows of the PDF content
    other_rows_data = [
        [''],
        [''],
        [Paragraph(f"<b> DRIVER SIGN IN FORM </b>", style_bold), ''],
        [Paragraph(f"Id: <b>{data.get('Id', 'N/A')}</b>", style_normal), ''],
        [Paragraph(f"Driver Name: <b>{data['First Name']} {data['Last Name']}</b>", style_normal), ''],
        [Paragraph(f"Date: <b>{data.get('Date', '_______________________')}</b>", style_normal), ''],
        # [Paragraph(f"First Name: <b>{data.get('First Name', 'N/A')}</b>", style_normal), ''],
        # [Paragraph(f"Last Name: <b>{data.get('Last Name', 'N/A')}</b>", style_normal), ''],
        [Paragraph(f"Phone: <b>{data.get('Phone', '_______________________')}</b>", style_normal), ''],
        [Paragraph(f"Carrier: <b>{data.get('Carrier', '_______________________')}</b>", style_normal), ''],
        [Paragraph(f"Broker: <b>{data['Broker']}</b>", style_normal), ''],
        [Paragraph(f"Customer PO # <b>{data['Customer PO #']}</b>", style_normal), ''],
        [Paragraph(f"Destination: <b>{data.get('Destination', '_______________________')}</b>", style_normal), ''],
        [Paragraph(f"Trailer/Container Number: <b>{data.get('Trailer/Container Number', '_______________________')}</b>",
                   style_normal), ''],
        [Paragraph(f"Vehicle Type: <b>{data.get('Vehicle Type', '_______________________')}</b>", style_normal), ''],
        [Paragraph(f"Scheduled Appointment Time: <b> {data.get('Scheduled Appointment Time', '_______________________')}</b>",
                   style_normal), ''],
        [Paragraph(f"Dispatcher Name: <b>{data.get('Dispatcher Name', '_______________________')}</b>", style_normal), ''],
        [Paragraph(f"Dispatcher Phone: <b>{data.get('Dispatcher Phone', '_______________________')}</b>", style_normal), ''],
        [Paragraph(f"Customer Name: <b>{data.get('Customer Name', 'N/A')}</b>", style_normal), ''],
        [Paragraph(f"Scanner: <b>{data.get('Scanner', '_______________________')}</b>", style_normal), ''],       
        [Paragraph(f"Loader:<b>_______________________</b>", style_normal), ''],
        [Paragraph(f"Dock In Time: <b>{data.get('Dock In Time', '_______________________')}</b>", style_normal), ''],
        [Paragraph(f"Dock Out Time: <b>{data.get('Dock Out Time', '_______________________')}</b>", style_normal), ''],
        [Paragraph(f"Timbers Used: <b>{data.get('Timbers Used', '_______________________')}</b>", style_normal), ''],
        [Paragraph(f"Poles Used: <b>{data.get('Poles Used', '_______________________')}</b>", style_normal), ''], 
        [Paragraph(f"Truck Assigned by: <b>________________________</b>", style_normal), '']
    ]

    # Create a table for other rows of data and set styles
    other_rows_table = Table(other_rows_data, colWidths=other_rows_widths)
    other_rows_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    # Add the other rows table and a spacer to the content
    content.append(other_rows_table)
    return content

if __name__ == "__main__":
    create_csv_file()  # Create the CSV file if it doesn't exist
    schedule.every().day.at("06:10").do(delete_csv_file_daily)

    while True:
        # Delete CSV file at 6:10 AM every morning
        delete_csv_file_daily()
        api_key = read_api_key(api_key_file_path)
        url = generate_dynamic_url()
        
        if api_key:
            data_list = fetch_data_from_api(url, api_key)
            if data_list:
                create_pdf(data_list)

        # Sleep for one minute (60 seconds) before the next iteration
        time.sleep(60)





#------------------------------------------------------------------------




# import json
# import os
# import pytz
# from datetime import datetime, timedelta
# from reportlab.lib.pagesizes import A4
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Image, Paragraph, PageBreak
# from reportlab.lib.styles import getSampleStyleSheet
# from reportlab.lib import colors
# from reportlab.lib.units import inch
# import requests
# import schedule
# import time
# from urllib.parse import quote

# # Define the JSON file to store generated data
# data_store_file = 'generated_data.json'
# api_key_file_path = 'apikey.txt'

# # Function to load generated data from JSON file
# def load_generated_data():
#     try:
#         with open(data_store_file, 'r') as file:
#             return json.load(file)
#     except FileNotFoundError:
#         return {}

# # Function to save generated data to JSON file
# def save_generated_data(data):
#     with open(data_store_file, 'w') as file:
#         json.dump(data, file, indent=4)

# # Function to delete the JSON file daily at 6:10 AM

# def delete_json_file_daily():
#     current_time = datetime.now(pytz.timezone('US/Eastern'))
#     if current_time.hour == 6 and current_time.minute == 10:
#         delete_json_file()


# # Function to delete the JSON file
# def delete_json_file():
#     try:
#         os.remove(data_store_file)
#         print(f"{data_store_file} deleted.")
#     except FileNotFoundError:
#         print(f"{data_store_file} not found.")
#     except Exception as e:
#         print(f"Error deleting {data_store_file}: {e}")

# # Function to generate the dynamic URL
# def generate_dynamic_url():
#     current_time = datetime.now()

#     # Calculate the starting time (today at 6:00 AM)
#     start_time = current_time.replace(hour=6, minute=0, second=0, microsecond=0)

#     # Calculate the ending time (tomorrow at 6:00 AM)
#     end_time = start_time + timedelta(days=1)

#     # Format the dates in the desired format and properly encode them
#     from_time = quote(start_time.strftime("%Y-%m-%dT%H:%M:%S+0000"))
#     to_time = quote(end_time.strftime("%Y-%m-%dT%H:%M:%S+0000"))

#     # Construct the URL
#     base_url = "https://api.waitwhile.com/v2/visits/export"
#     params = {
#         "format": "JSON",
#         "fromTime": from_time,
#         "toTime": to_time,
#         "dateRangeField": "created"
#     }
#     url = f"{base_url}?{'&'.join([f'{key}={value}' for key, value in params.items()])}"
#     print(url)

#     return url

# # Function to convert UTC time to Eastern Time (EST)
# def convert_utc_to_est(utc_time_string):
#     if utc_time_string == 'N/A':
#         return 'N/A'

#     try:
#         utc_timezone = pytz.timezone('UTC')
#         est_timezone = pytz.timezone('US/Eastern')
#         utc_time = datetime.strptime(utc_time_string, "%Y-%m-%dT%H:%M:%S.%fZ")
#         utc_time = utc_timezone.localize(utc_time)
#         est_time = utc_time.astimezone(est_timezone)
#         return est_time.strftime("%Y-%m-%d %H:%M:%S %Z")
#     except ValueError as e:
#         print(f"Error parsing UTC time: {e}")
#         return "N/A"

# # Function to get the first element from a list or return 'N/A'
# def get_first_element(lst):
#     if lst:
#         return lst[0]
#     return '_______________________'

# # Function to read API key from a text file
# def read_api_key(api_key_file_path):
#     try:
#         with open(api_key_file_path, 'r') as file:
#             return file.read().strip()
#     except FileNotFoundError:
#         print(f"Error: The file '{api_key_file_path}' was not found.")
#         return None

# # Function to fetch data from the API
# def fetch_data_from_api(url, api_key):
#     try:
#         headers = {"apikey": api_key}
#         response = requests.get(url, headers=headers)
#         if response.status_code == 200:
#             data_list = response.json()
#             if isinstance(data_list, dict):
#                 data_list = [data_list]
#             return data_list
#         else:
#             print(f"Failed to fetch data from the API. Status code: {response.status_code}")
#     except Exception as e:
#         print(f"Error fetching data from the API: {e}")
#     return []
# # Function to create a PDF
# def create_pdf(data_list):
#     try:
#         # Define styles for the content
#         styles = getSampleStyleSheet()
#         style_normal = styles['Normal']
#         style_bold = styles['Heading1']
#         style_normal.fontSize = 15
#         style_normal.leading = 16

#         # Define page layout parameters
#         page_width, page_height = A4
#         margin = 40
#         logo_height = 100
#         available_space = page_width - 2 * margin
#         first_row_widths = [available_space * 0.5, available_space * 0.5]
#         other_rows_widths = [available_space * 0.9, available_space * 0.1]

#         # Create a directory to store PDF files
#         exported_path='//multimedia/multimedia/SKAPS/Skaps2023/P-S'
#         base_directory=exported_path
#         current_date = datetime.now()
#         year_folder_name = f"Shipping {current_date.year}"
#         waitwhile_folder_name = "Waitwhile"
#         month_folder_name = current_date.strftime('%B')  # Month name
#         day_folder_name = current_date.strftime('%Y-%m-%d')
#         year_folder_path = os.path.join(base_directory, year_folder_name)
#         waitwhile_folder_path = os.path.join(year_folder_path, waitwhile_folder_name)
#         month_folder_path = os.path.join(waitwhile_folder_path, month_folder_name)
#         day_folder_path = os.path.join(month_folder_path, day_folder_name)
#         os.makedirs(day_folder_path, exist_ok=True)



#         # Load generated data from JSON file
#         generated_data = load_generated_data()

#         # Iterate through data and create/update PDFs
#         for counter, record in enumerate(data_list, start=1):
#             record_id = record.get('id', 'N/A')
#             updated_ist = convert_utc_to_est(record.get('updated', 'N/A'))
#             waitlist_time_ist = convert_utc_to_est(record.get('waitlistTime', 'N/A'))
#             serve_time_ist = convert_utc_to_est(record.get('serveTime', 'N/A'))

#             # Check if the record ID is already in the generated data
#             if record_id in generated_data:
#                 # Check if the "updated" field has changed
#                 if generated_data[record_id] == updated_ist:
#                     print(f"Skipping PDF generation for record ID {record_id}.")
#                     continue  # Skip PDF generation
#                         # Convert 'waitlistTime' and 'serveTime' to Eastern Time (EST)


#             # Iterate through data and create PDFs
#             fetched_data = {
#                 'Id': record.get('id', 'N/A'),
#                 'Date': convert_utc_to_est(record.get('created', 'N/A')),
#                 'First Name': record.get('firstName', 'N/A'),
#                 'Last Name': record.get('lastName', 'N/A'),
#                 'Phone': record.get('phone', 'N/A'),
#                 'Country': record.get('country', 'N/A'),
#                 'City': record.get('city', 'N/A'),
#                 'Carrier': get_first_element(record['fields'].get('tcY1X5Kb7h2uIWK53Lyg', [])),
#                 'Vehicle Type': get_first_element(record['fields'].get('i1I6xyqqxa6oTlE3DkYM', [])),
#                 'Trailer/Container Number': get_first_element(record['fields'].get('uMvYMV9AWZ1OGIbA1JKn', [])),
#                 'Destination': get_first_element(record['fields'].get('fikIvjiydrX5ofr6RvNi', [])),
#                 'Broker': get_first_element(record['fields'].get('NIzqc21iVthkg02MTLGG', [])),
#                 'Scheduled Appointment Time': get_first_element(record['fields'].get('7vccTLW6wx0uJTI8pTGV', [])),
#                 'Customer Name': get_first_element(record['fields'].get('60kWvZTF6SNkCEECXi66', [])),
#                 'Scanner': get_first_element(record['fields'].get('vGcgWk6xCnY3CjQuEgxa', [])),
#                 'Customer PO #': get_first_element(record['fields'].get('L325nfBjUROuGPa3qUJu', [])),
#                 'Dispatcher Name': get_first_element(record['fields'].get('w22E7B7dLi4SYeXxgzLG', [])),
#                 'Dispatcher Phone': get_first_element(record['fields'].get('ot2ggPrasvp776PDLArX', [])),
#                 'Dock In Time': get_first_element(record['fields'].get('8WHDY3nMaW2GlARauOn5', [])),
#                 'Dock Out Time': get_first_element(record['fields'].get('BkDnZV8ZKyp8CH0oBacG', [])),
#                 'Poles Used': get_first_element(record['fields'].get('DAFP7BsGgqUest0w98tL', [])),
#                 'Timbers Used': get_first_element(record['fields'].get('RX6CchYy0g2NCGDu8wqx', [])),
#             }


            
#             # Check if 'waitlistTime' is not 'N/A' and 'serveTime' is 'N/A'
#             if (waitlist_time_ist != 'N/A' and serve_time_ist == 'N/A') or serve_time_ist != 'N/A':
#                 try:
#                     # Define the PDF file path based on record information
#                     pdf_file = os.path.join(day_folder_path, f"{fetched_data.get('First Name', 'N/A')}_{fetched_data.get('Last Name', 'N/A')}_{fetched_data.get('Phone', 'N/A')}.pdf")
#                     # Create a SimpleDocTemplate for the PDF
#                     doc = SimpleDocTemplate(pdf_file, pagesize=A4)
#                     # Generate content for the PDF using the create_content_block function
#                     content_list = create_content_block(fetched_data, style_normal, style_bold, available_space,
#                                                         first_row_widths, other_rows_widths, logo_height)
#                     # Build the PDF with the generated content
#                     doc.build(content_list)
#                     # Print a message indicating that the PDF has been saved
#                     print(f'PDF saved at {pdf_file}')
#                     # Update the generated_data dictionary with the current record's ID and timestamp
#                     generated_data[record_id] = updated_ist
#                     # Save the updated generated_data to the JSON file
#                     save_generated_data(generated_data)
#                 except PermissionError:
#                     # If a PermissionError occurs, create a new PDF with an incremented name
#                     pdf_file = None
#                     counter_suffix = 1
#                     while pdf_file is None or os.path.exists(pdf_file):
#                         # Generate a new PDF file name with an incremented counter_suffix
#                         pdf_file = os.path.join(day_folder_path, f"{fetched_data.get('First Name', 'N/A')}_{fetched_data.get('Last Name', 'N/A')}_{fetched_data.get('Phone', 'N/A')}_{counter_suffix}.pdf")
#                         counter_suffix += 1

#                     # Create a SimpleDocTemplate for the new PDF
#                     doc = SimpleDocTemplate(pdf_file, pagesize=A4)
#                     # Generate content for the PDF using the create_content_block function
#                     content_list = create_content_block(fetched_data, style_normal, style_bold, available_space,
#                                                         first_row_widths, other_rows_widths, logo_height)
#                     # Build the new PDF with the generated content
#                     doc.build(content_list)
#                     # Print a message indicating that the new PDF has been saved
#                     print(f'PDF saved at {pdf_file}')
#                     # Update the generated_data dictionary with the current record's ID and timestamp
#                     generated_data[record_id] = updated_ist
#                     # Save the updated generated_data to the JSON file
#                     save_generated_data(generated_data)

#     except Exception as e:
#         print(f"Error creating PDF: {e}")

# # Function to create content for the PDF
# def create_content_block(data, style_normal, style_bold, available_space, first_row_widths, other_rows_widths, logo_height):
#     content = []

#     # Define data for the first row of the PDF content
#     first_row_data = [
#         [Image('skaps_logo.png', width=100, height=logo_height), Paragraph("<b>SKAPS INDUSTRIES</b>",
#                                                                          style_bold)],
#     ]

#     # Create a table for the first row data and set styles
#     first_row_table = Table(first_row_data, colWidths=first_row_widths)
#     first_row_table.setStyle(TableStyle([
#         ('ALIGN', (0, 0), (0, 1), 'LEFT'),
#         ('ALIGN', (1, 0), (1, 1), 'RIGHT'),
#         ('VALIGN', (0, 0), (1, 1), 'MIDDLE'),
#     ]))

#     # Add the first row table and a spacer to the content
#     content.append(first_row_table)
#     content.append(Spacer(1, 20))

#     # Define data for other rows of the PDF content
#     # Define data for other rows of the PDF content
#     other_rows_data = [
#         [''],
#         [''],
#         [Paragraph(f"<b> DRIVER SIGN IN FORM </b>", style_bold), ''],
#         [Paragraph(f"Id: <b>{data.get('Id', 'N/A')}</b>", style_normal), ''],
#         [Paragraph(f"Driver Name: <b>{data['First Name']} {data['Last Name']}</b>", style_normal), ''],
#         [Paragraph(f"Date: <b>{data.get('Date', '_______________________')}</b>", style_normal), ''],
#         # [Paragraph(f"First Name: <b>{data.get('First Name', 'N/A')}</b>", style_normal), ''],
#         # [Paragraph(f"Last Name: <b>{data.get('Last Name', 'N/A')}</b>", style_normal), ''],
#         [Paragraph(f"Phone: <b>{data.get('Phone', '_______________________')}</b>", style_normal), ''],
#         [Paragraph(f"Carrier: <b>{data.get('Carrier', '_______________________')}</b>", style_normal), ''],
#         [Paragraph(f"Broker: <b>{data['Broker']}</b>", style_normal), ''],
#         [Paragraph(f"Customer PO # <b>{data['Customer PO #']}</b>", style_normal), ''],
#         [Paragraph(f"Destination: <b>{data.get('Destination', '_______________________')}</b>", style_normal), ''],
#         [Paragraph(f"Trailer/Container Number: <b>{data.get('Trailer/Container Number', '_______________________')}</b>",
#                    style_normal), ''],
#         [Paragraph(f"Vehicle Type: <b>{data.get('Vehicle Type', '_______________________')}</b>", style_normal), ''],
#         [Paragraph(f"Scheduled Appointment Time: <b> {data.get('Scheduled Appointment Time', '_______________________')}</b>",
#                    style_normal), ''],
#         [Paragraph(f"Dispatcher Name: <b>{data.get('Dispatcher Name', '_______________________')}</b>", style_normal), ''],
#         [Paragraph(f"Dispatcher Phone: <b>{data.get('Dispatcher Phone', '_______________________')}</b>", style_normal), ''],
#         [Paragraph(f"Customer Name: <b>{data.get('Customer Name', 'N/A')}</b>", style_normal), ''],
#         [Paragraph(f"Scanner: <b>{data.get('Scanner', '_______________________')}</b>", style_normal), ''],       
#         [Paragraph(f"Loader:<b>_______________________</b>", style_normal), ''],
#         [Paragraph(f"Dock In Time: <b>{data.get('Dock In Time', '_______________________')}</b>", style_normal), ''],
#         [Paragraph(f"Dock Out Time: <b>{data.get('Dock Out Time', '_______________________')}</b>", style_normal), ''],
#         [Paragraph(f"Timbers Used: <b>{data.get('Timbers Used', '_______________________')}</b>", style_normal), ''],
#         [Paragraph(f"Poles Used: <b>{data.get('Poles Used', '_______________________')}</b>", style_normal), ''], 
#         [Paragraph(f"Truck Assigned by: <b>________________________</b>", style_normal), '']
#     ]

#     # Create a table for other rows of data and set styles
#     other_rows_table = Table(other_rows_data, colWidths=other_rows_widths)
#     other_rows_table.setStyle(TableStyle([
#         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#         ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
#     ]))

#     # Add the other rows table and a spacer to the content
#     content.append(other_rows_table)
#     return content

# if __name__ == "__main__":
#     schedule.every().day.at("06:10").do(delete_json_file_daily)

#     while True:
#         # Delete JSON file at 6:10 AM every morning
#         delete_json_file_daily()
#         api_key = read_api_key(api_key_file_path)
#         url = generate_dynamic_url()
        
#         if api_key:
#             data_list = fetch_data_from_api(url, api_key)
#             if data_list:
#                 create_pdf(data_list)

#         # Sleep for one minute (60 seconds) before the next iteration
#         time.sleep(60)

