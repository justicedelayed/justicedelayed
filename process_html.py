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
    # print("all_CNR_HTMLS: ", all_CNR_HTMLS)
    connection = None
    try:
        connection = setup_db()
        # print("Connection is")
    except Exception as e:
        logging.info(f"Error setting up database: {e}")

    # drop CNR table
    # drop_CNR_table(connection)

    # Fetch the HTML content from the database
    if connection:
        court_pages = fetch_court_pages(connection)

        if court_pages:
            for page in court_pages[7:8]:
                (
                    id,
                    state_code,
                    district_code,
                    court_name,
                    establishment_name,
                    html_content,
                ) = page
                html_content_with_triple_quotes = f'"""{html_content}"""'
                print("Processing court page:", court_name)
                print("Establishment Name:", establishment_name)
                print("State Code:", state_code)
                print("District Code:", district_code)
                # print("HTML: ", (html_content_with_triple_quotes[:500]))
                all_CNR = parse_html_files(html_content_with_triple_quotes)
                print("All CNR: ", all_CNR)
                # Iterate over each list in all_CNR_HTMLS
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
                        INSERT INTO CNR (date_processed, state_code, district_code, court_name, establishment_name, case_type_number_year, petitioner_responder, cnr_number)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            date_processed,
                            state_code,
                            district_code,
                            court_name,
                            establishment_name,
                            case_type_number_year,
                            petitioner_responder,
                            cnr_number,
                        ),
                    )
                    connection.commit()
                    cursor.close()
                    all_CNR_HTMLS.append(cnr_list)
                # print("First CNR: ", all_CNR[81])
                # print("Length of CNR: ", len(all_CNR))
                # print("All CNR: ", all_CNR)
                # print("All CNR HTMLS", all_CNR_HTMLS)
                # all_CNR_HTMLS.append(all_CNR)
                # print("CNR Numbers: ", all_CNR_HTMLS)
                # print("Length of CNR Numbers: ", len(all_CNR_HTMLS))
                # print("First CNR Number: ", all_CNR_HTMLS[0])

        # After processing all files, save the results to a CSV file (optional)
        # output_df = pd.DataFrame(
        #     all_CNR_HTMLS,
        #     columns=["Case_Type_Number_Year", "Petitioner_Responder", "CNR_Number"],
        # )

        # print("Output DF: ", output_df.head())

        # output_df.to_csv("CNR_numbers.csv", index=False)

        print(
            "Processing complete. CNR numbers extracted and saved to 'CNR_numbers.csv'."
        )

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
                    # print("HERE IN ELEMENTS")
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


# # Specify the directory containing the HTML files
# # directory = "/Users/shalakashinde/Columbia/master_project/court_page_htmls"

# # List all files in the directory
# files = os.listdir(directory)

# # Iterate over the HTML files
# for file_name in files:
#     # Construct the full file path
#     file_path = os.path.join(directory, file_name)

#     try:
#         # Read the file content
#         with open(file_path, "r", encoding="utf-8") as file:
#             html_content = file.read()
#     except Exception as e:
#         print(f"Error reading file {file_name}: {e}")
#         continue


if __name__ == "__main__":
    main()
