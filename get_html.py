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
    fetch_acts_rows,
    save_html_to_db,
    create_html_table,
)
import datetime
import os

# Configure logging
logging.basicConfig(
    filename="court_navigator.log",  # Log to this file
    level=logging.INFO,  # Log all INFO level and above
    format="%(asctime)s - %(levelname)s - %(message)s",  # Include timestamp
)


def get_html_content(
    connection=None,
    state_code="28",
    district_code="1",
    court_complex_code="1280004",
    est_code="",
    act_code="",
):

    # Get today's date
    date_scraped = datetime.date.today()
    logging.basicConfig(level=logging.INFO)

    # Define the URL
    url = "https://services.ecourts.gov.in/ecourtindia_v6/?p=casestatus/submitAct"

    # Define the headers
    headers = {
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }

    # Define the data (parameters)
    data = {
        "search_act": "",
        "actcode": act_code,
        "under_sec": "302",
        "case_status": "Pending",
        "act_captcha_code": "",
        "state_code": state_code,
        "dist_code": district_code,
        "court_complex_code": court_complex_code,
        "est_code": est_code,
        "ajax_req": "true",
        "app_token": "",
    }

    # Send the POST request
    response = requests.post(url, headers=headers, data=data)

    # Print the response
    print("Status Code:", response.status_code)

    if response.status_code == 200:
        print("Request Successful")

        response_text = response.text
        # Parse the JSON response

        if not response_text:
            logging.error("Response text is None.")
            save_html_to_db(
                connection,
                date_scraped,
                state_code,
                district_code,
                court_complex_code,
                est_code,
                act_code,
                "Pending",
                "E006: No Records found",
            )
        else:
            # Parse the JSON response
            response_data = json.loads(response_text)

            # Extract the act_data HTML
            act_data = response_data.get("act_data", "")

            save_html_to_db(
                connection,
                date_scraped,
                state_code,
                district_code,
                court_complex_code,
                est_code,
                act_code,
                "Pending",
                act_data,
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
    # drop_table(connection, "Acts")
    create_html_table(connection)
    date_scraped = datetime.date.today()
    logging.info("COURTS_HTML Table created.")
    rows = fetch_acts_rows(connection)
    if rows:
        for row in rows:
            state_code = row[2]
            district_code = row[3]
            court_code = row[4]
            est_code = row[5]
            act_code = row[6]
            act_name = row[7]
            if act_code == "E005: No Act Codes list found":
                save_html_to_db(
                    connection,
                    date_scraped,
                    state_code,
                    district_code,
                    court_code,
                    est_code,
                    "E005: No Act Codes list found",
                    "Pending",
                    "E005: No Act Codes list found",
                )
            else:
                print(
                    f"State Code: {state_code}, District Name: {district_code}, Court Code: {court_code}, Establishment Code: {est_code}, Act Code: {act_code}, Act Name: {act_name}"
                )
                get_html_content(
                    connection=connection,
                    state_code=state_code,
                    district_code=district_code,
                    court_complex_code=court_code,
                    est_code=est_code,
                    act_code=act_code,
                )
            print("Processing next ACT row.")
            # break
    else:
        logging.error("No rows found.")


if __name__ == "__main__":
    main()
