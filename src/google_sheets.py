def read_sheet(sheet_id: str, sheets_service):
    # Define the range to read from
    range_ = "Sheet1!A:A"  # Adjust this if your data is in a different sheet or column

    # Read the data from the sheet
    result = sheets_service.spreadsheets().values().get(
        spreadsheetId=sheet_id,
        range=range_
    ).execute()

    # Extract the folder names from the response
    values = result.get('values', [])  # 'values' is a list of lists

    # Flatten the list of lists and return only the folder names
    values = [value[0] for value in values if value]  # Handle potential empty rows

    return values

def add_value_to_sheet(value: str, sheet_id: str, sheets_service):
    # Specify the range for appending data
    range_ = "Sheet1!A:A"  # Adjust the sheet name and range as needed

    # Define the data to append
    values = [[value]]
    body = {'values': values}

    # Append the data to the sheet
    sheets_service.spreadsheets().values().append(
        spreadsheetId=sheet_id,
        range=range_,
        valueInputOption="RAW",
        body=body
    ).execute()