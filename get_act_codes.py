import requests
import re
from bs4 import BeautifulSoup
import json
import logging
from db2 import (
    save_acts_to_db,
    create_act_table,
    create_connection,
    drop_table,
    fetch_court_rows,
)
import datetime
import os

# Enable logging


def get_act_codes(
    connection=None,
    state_code="28",
    district_code="1",
    court_complex_code="1280004",
    est_code="",
):

    # Get today's date
    date_scraped = datetime.date.today()
    logging.basicConfig(level=logging.INFO)

    # Define the URL
    url = "https://services.ecourts.gov.in/ecourtindia_v6/?p=casestatus/fillActType"

    # Define the headers
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }

    # Define the data (parameters)
    data = {
        "state_code": state_code,
        "dist_code": district_code,
        "court_complex_code": court_complex_code,
        "est_code": est_code,
        "search_act": "",
        "ajax_req": "true",
        "app_token": "",
    }

    # Send the POST request
    response = requests.post(url, headers=headers, data=data)

    # Print the response
    print("Status Code:", response.status_code)
    print("Response Text:", response.text)

    if response.status_code == 200:
        print("Request Successful")

        response_text = response.text

        # Parse the JSON response
        response_data = json.loads(response_text)

        # Extract the act_list HTML
        act_list_html = response_data.get("act_list", "")

        # Use BeautifulSoup to parse the HTML options
        soup = BeautifulSoup(act_list_html, "html.parser")

        # Initialize an empty dictionary for storing the ACT codes and their corresponding details
        filtered_act_dict = {}

        # Compile your regex for filtering act names
        ipc_regex = re.compile(r"^(I.P.C|IPC|Indian Penal Code)\b.*$", re.IGNORECASE)

        options = soup.find_all("option")
        print("Number of Options:", len(options))

        # Loop through each <option> tag and extract the value and text
        for index, option in enumerate(soup.find_all("option")):
            act_code = option.get("value")
            act_name = option.text.strip()

            # Apply regex filtering
            if act_code and act_name and act_code != "" and ipc_regex.search(act_name):
                logging.info(f"REGEX MATCHED: {act_name}")
                save_acts_to_db(
                    connection,
                    date_scraped,
                    state_code,
                    district_code,
                    court_complex_code,
                    est_code,
                    act_code,
                    act_name,
                )


def setup_db():
    # Create a connection to the local SQLite database
    db_file = "jd-master-db.db"
    if os.path.exists(db_file):
        connection = create_connection(db_file)
    else:
        logging.error("Database file does not exist.")
        connection = create_connection(db_file)
    if not connection:
        return
    else:
        logging.info("Connection to SQLite database established.")

    # return self.connection
    return connection


def main():
    connection = setup_db()
    drop_table(connection, "Acts")
    create_act_table(connection)
    logging.info("ACT Table created.")
    rows = fetch_court_rows(connection)
    if rows:
        for row in rows:
            print("row is: ", type(row))
            state_code = row[2]
            district_code = row[3]
            court_code = row[4]
            court_name = row[5]
            est_code = row[6]
            est_name = row[7]
            print(court_code)
            court_code = court_code.split("@")[0]
            print(court_code)
            if est_code == "E003: No court establishment found":
                est_code = ""
            print(
                f"State Code: {state_code}, District Name: {district_code}, Court Code: {court_code}, Establishment Code: {est_code}"
            )
            get_act_codes(
                connection=connection,
                state_code=state_code,
                district_code=district_code,
                court_complex_code=court_code,
                est_code=est_code,
            )
            print("Processing next row.")
            # break
    else:
        logging.error("No rows found.")


if __name__ == "__main__":
    main()
