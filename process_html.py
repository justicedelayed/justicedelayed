import os
import pandas as pd
from bs4 import BeautifulSoup
from db2 import fetch_court_pages, create_connection, create_cnr_table, drop_table
import logging
import datetime as dt


def drop_CNR_table(connection):
    drop_table(connection, "CNR")


def setup_db():
    # Create a connection to the local SQLite database
    db_file = "jd-master-db.db"
    if os.path.exists(db_file):
        connection = create_connection(db_file)
    else:
        print("Database file does not exist.")
        connection = create_connection(db_file)
    if not connection:
        return
    else:
        # create table
        create_cnr_table(connection)
        print("Connection to SQLite database established and CNR Table created.")
    return connection


def main():
    # Initialize an empty list to store CNR numbers
    date_processed = dt.datetime.now().strftime("%Y-%m-%d %H:%M %p")
    all_CNR_HTMLS = [["Case_Type_Number_Year", "Petitioner_Responder", "CNR_Number"]]
    connection = None
    try:
        connection = setup_db()
    except Exception as e:
        logging.info(f"Error setting up database: {e}")

    # drop CNR table
    # drop_CNR_table(connection)

    # Fetch the HTML content from the database
    if connection:
        rows = fetch_court_pages(connection)
        if rows:
            for row in rows:
                date_scraped = row[1]
                state_code = row[2]
                district_code = row[3]
                court_code = row[4]
                est_code = row[5]
                act_code = row[6]
                case_status = row[7]
                html_content = row[8]
                section_number = row[9]
                html_content_with_triple_quotes = f'"""{html_content}"""'
                print(
                    f"State Code: {state_code}, District Name: {district_code}, Court Code: {court_code}, Establishment Code: {est_code}, Act Code: {act_code}, Section Number: {section_number}"
                )
                all_CNR = parse_html_files(html_content_with_triple_quotes)
                print("All CNR: ", all_CNR)
                # Iterate over each list in all_CNR_HTMLS
                if all_CNR == []:
                    # Insert the values with error code into the database table
                    cursor = connection.cursor()
                    cursor.execute(
                        """
                        INSERT INTO CNR (date_processed, date_scraped, state_code, district_code, court_code, est_code, act_code, section_number, case_status, case_type_number_year, petitioner_responder, cnr_number)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            date_processed,
                            date_scraped,
                            state_code,
                            district_code,
                            court_code,
                            est_code,
                            act_code,
                            section_number,
                            case_status,
                            "E007: No CNR numbers found as No Records Found",
                            "E007: No CNR numbers found as No Records Found",
                            "E007: No CNR numbers found as No Records Found",
                        ),
                    )
                    connection.commit()
                    cursor.close()
                else:
                    for cnr_list in all_CNR:
                        print("CNR List: ", cnr_list)
                        # Extract the values from the list
                        case_type_number_year = cnr_list[0]
                        petitioner_responder = cnr_list[1]
                        cnr_number = cnr_list[2]

                        # Insert the values into the database table
                        cursor = connection.cursor()
                        cursor.execute(
                            """
                            INSERT INTO CNR (date_processed, date_scraped, state_code, district_code, court_code, est_code, act_code, section_number, case_status, case_type_number_year, petitioner_responder, cnr_number)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                            (
                                date_processed,
                                date_scraped,
                                state_code,
                                district_code,
                                court_code,
                                est_code,
                                act_code,
                                section_number,
                                case_status,
                                case_type_number_year,
                                petitioner_responder,
                                cnr_number,
                            ),
                        )
                        connection.commit()
                        cursor.close()
                    all_CNR_HTMLS.append(cnr_list)

        print("Processing complete. CNR numbers extracted and saved to CNR Table.")

    else:
        logging.error("No connection to database.")


def parse_html_files(html_content):
    # Parse the HTML content using BeautifulSoup

    onclick_value = None
    all_CNR_2 = []
    soup = BeautifulSoup(html_content, "html.parser")

    # Find all "table" tags
    table_tags = soup.find_all("table")

    # print("Table tags: ", table_tags)

    if table_tags:
        for each_table in table_tags:
            # print("here")
            pretty_table = each_table.prettify()

            # Re-parse the pretty table to search for specific elements
            soup_doc = BeautifulSoup(pretty_table, "html.parser")

            # Find all elements with class "someclass"
            # elements_with_someclass = soup_doc.find_all("a", class_="someclass")

            # print("ELements with somclass as class ", elements_with_someclass)

            all_trs = soup_doc.find_all("tr")

            # trs_with_case_info = []
            # trs_with_court_name = []

            # for tr in all_trs:

            #     if len(tr) > 2:
            #         tds_with_case_info.append(td)
            #         td[]

            rows = all_trs

            # print("all_rows: ", all_trs)

            for row in rows:
                all_CNR = []
                # print("HERE in row")
                # print("Row: ", row)
                columns = row.find_all("td")  # This will give you a list of columns
                if not columns:
                    # print("HERE IN TH")
                    columns = row.find_all(
                        "th"
                    )  # This will give you a list of columns from headers
                # print("FINDING TDS")
                # print("Columns: ", columns)
                print("Length of columns: ", len(columns))
                if len(columns) >= 3:
                    case_type_number_year = columns[1].text.strip()
                    petitioner_vs_respondent = (
                        columns[2]
                        .text.replace("<br/>", " ")
                        .replace("Vs", " Vs ")
                        .strip()
                    )
                    # print("Case Type Number Year: ", case_type_number_year)
                    # print("Petitioner vs respondent ", petitioner_vs_respondent)
                    all_CNR.append(case_type_number_year)
                    all_CNR.append(petitioner_vs_respondent)

                    i = 1
                    # print("ALL CNR: ", all_CNR)
                    # Find all elements with class "someclass"
                    elements_with_someclass = columns[3].find_all(
                        "a", class_="someclass"
                    )

                    if not elements_with_someclass:
                        print("No elements with someclass found.")
                        all_CNR.append("E004: No CNR found")

                    for element in elements_with_someclass:
                        # print("Loop counter: ", i)
                        # print(" HERE IN ELEMENTS")
                        onclick_value = element.get("onclick")

                        # Extract the CNR number from the onclick attribute
                        data_values = onclick_value.split("'")[
                            1:-1
                        ]  # This will give you a list of data values
                        CNR_number = data_values[0]
                        # print("CNR Number: ", CNR_number)
                        i += 1

                        # Add the CNR number to the list
                        all_CNR.append(CNR_number)
                        # print("First CNR: ", all_CNR[0])

                    # print("All CNR: ", all_CNR)
                    all_CNR_2.append(all_CNR)
                    # print("First CNR: ", all_CNR_2[0])
    else:
        print(f"No tables found in the HTML file. ")

    print("Sending all CNR 2: ", all_CNR_2)

    return all_CNR_2


if __name__ == "__main__":
    main()
