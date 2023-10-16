from datetime import datetime, timedelta
from urllib.parse import quote

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

    return url

# Call the function to generate the URL and print it
url = generate_dynamic_url()
print(url)


# Call the function to generate the URL and print it
url = generate_dynamic_url()
print(url)



waitwhile_url="https://api.waitwhile.com/v2/visits/export?format=JSON&fromTime=2023-10-01T06%3A00%3A00%2B0000&toTime=2023-10-02T06%3A00%3A00%2B0000&dateRangeField=created"

if waitwhile_url == url:
    print("Both are same")
else :
    print("both are different")