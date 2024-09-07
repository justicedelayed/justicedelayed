import os
import pandas as pd
from bs4 import BeautifulSoup
from db2 import fetch_court_pages, create_connection
import logging


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
        print("Connection to SQLite database established.")
    return connection


def main():

    # Initialize an empty list to store CNR numbers
    all_CNR_HTMLS = [["Case_Type_Number_Year", "Petitioner_Responder", "CNR_Number"]]
    print("all_CNR_HTMLS: ", all_CNR_HTMLS)
    connection = None
    try:
        connection = setup_db()
        print("Connection is")
    except Exception as e:
        logging.info(f"Error setting up database: {e}")

    # Fetch the HTML content from the database
    if connection:
        court_pages = fetch_court_pages(connection)

        if court_pages:
            for page in court_pages[5:9]:
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
                print("HTML: ", (html_content_with_triple_quotes[:500]))
                all_CNR = parse_html_files(html_content_with_triple_quotes)
                print("All CNR: ", all_CNR)
                print("All CNR HTMLS", all_CNR_HTMLS)
                all_CNR_HTMLS.append(all_CNR)
                # print("CNR Numbers: ", all_CNR)

        # After processing all files, save the results to a CSV file (optional)
        output_df = pd.DataFrame(
            all_CNR_HTMLS,
            columns=["Case_Type_Number_Year", "Petitioner_Responder", "CNR_Number"],
        )

        NEW TABLE : 
       [ state_code, district_code, court_name, establishment_name, "Case_Type_Number_Year", "Petitioner_Responder", "CNR_Number" ]

        # print("Output DF: ", output_df.head())

        output_df.to_csv("CNR_numbers.csv", index=False)

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
            print("here")
            pretty_table = each_table.prettify()

            # Re-parse the pretty table to search for specific elements
            soup_doc = BeautifulSoup(pretty_table, "html.parser")

            # Find all elements with class "someclass"
            elements_with_someclass = soup_doc.find_all("a", class_="someclass")

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
                print("HERE in row")
                # print("Row: ", row)
                columns = row.find_all("td")  # This will give you a list of columns
                if not columns:
                    columns = row.find_all(
                        "th"
                    )  # This will give you a list of columns from headers
                print("FINDING TDS")
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
                    all_CNR.append(case_type_number_year)
                    all_CNR.append(petitioner_vs_respondent)
                    for element in elements_with_someclass:
                        # print(" HERE IN ELEMENTS")
                        onclick_value = element.get("onclick")

                    # Extract the CNR number from the onclick attribute
                    data_values = onclick_value.split("'")[
                        1:-1
                    ]  # This will give you a list of data values
                    CNR_number = data_values[0]
                    # print("CNR Number: ", CNR_number)

                    # Add the CNR number to the list
                    all_CNR.append(CNR_number)

                    # print("All CNR: ", all_CNR)
                    all_CNR_2.append(all_CNR)
    else:
        print(f"No tables found in the HTML file. ")

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
