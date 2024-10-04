import sqlite3
from sqlite3 import Error


# Function to create a connection to the SQLite database
def create_connection(db_file):
    connection = None
    try:
        connection = sqlite3.connect(db_file)
        print(f"Connected to SQLite database: {db_file}")
    except Error as e:
        print(f"Error connecting to SQLite: {e}")
    return connection


# Function to create a table
def create_table(connection):
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS States (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        state_name TEXT NOT NULL,
        state_code TEXT NOT NULL
    )
    """
    try:
        cursor = connection.cursor()
        cursor.execute(create_table_sql)
        connection.commit()
        print("Table 'States' created successfully.")
    except Error as e:
        print(f"Error creating table: {e}")


def create_district_table(connection):
    print("Creating district table from here")
    create_table_sql = """
        CREATE TABLE IF NOT EXISTS Districts (
            state_code TEXT NOT NULL,
            district_name TEXT NOT NULL,
            district_code TEXT NOT NULL
        )
        """
    try:
        cursor = connection.cursor()
        cursor.execute(create_table_sql)
        connection.commit()
        print("Table created successfully.")
    except Error as e:
        print(f"Error creating table: {e}")


# Function to create the HTML storage table
def create_html_table(connection):
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS COURTS_HTML (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_scraped TEXT NOT NULL,
        state_code TEXT NOT NULL,
        district_code TEXT NOT NULL,
        court_code TEXT NOT NULL,
        establishment_code TEXT NOT NULL,
        act_code TEXT NOT NULL,
        case_status TEXT NOT NULL,
        html_content TEXT NOT NULL
    )
    """
    try:
        cursor = connection.cursor()
        cursor.execute(create_table_sql)
        connection.commit()
        print("Table 'COURTS_HTML' created successfully.")
    except Error as e:
        print(f"Error creating table: {e}")


# Function to create the HTML storage table
def create_cnr_table(connection):
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS CNR (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_processed TEXT NOT NULL,
        date_scraped TEXT NOT NULL,
        state_code TEXT NOT NULL,
        district_code TEXT NOT NULL,
        court_code TEXT NOT NULL,
        est_code TEXT NOT NULL,
        act_code TEXT NOT NULL,
        section_number TEXT NOT NULL,
        case_status TEXT NOT NULL,
        case_type_number_year TEXT NOT NULL,
        petitioner_responder TEXT NOT NULL, 
        cnr_number TEXT NOT NULL
    )
    """
    try:
        cursor = connection.cursor()
        cursor.execute(create_table_sql)
        connection.commit()
        print("Table 'CNR' created successfully.")
    except Error as e:
        print(f"Error creating table: {e}")


# Function to save to the HTML storage table
def save_html_to_db(
    connection,
    date_scraped,
    state_code,
    district_code,
    court_code,
    establishment_code,
    act_code,
    case_status,
    html_content,
):
    insert_sql = """
    INSERT INTO COURTS_HTML(date_scraped, state_code, district_code, court_code, establishment_code, act_code, case_status, html_content)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    try:
        cursor = connection.cursor()
        cursor.execute(
            insert_sql,
            (
                date_scraped,
                state_code,
                district_code,
                court_code,
                establishment_code,
                act_code,
                case_status,
                html_content,
            ),
        )
        connection.commit()
        print(f"HTML content saved successfully.")
    except Error as e:
        print(f"Error saving HTML content to database: {e}")


# Function to create the HTML storage table
def create_court_table(connection):
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS Courts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_scraped TEXT NOT NULL,
        state_code TEXT NOT NULL,
        district_code TEXT NOT NULL,
        court_code TEXT NOT NULL,
        court_name TEXT NOT NULL,
        establishment_code TEXT,
        establishment_name TEXT
    )
    """
    try:
        cursor = connection.cursor()
        cursor.execute(create_table_sql)
        connection.commit()
        print("Table 'Courts' created successfully.")
    except Error as e:
        print(f"Error creating table: {e}")


# Function to create the HTML storage table
def create_act_table(connection):
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS Acts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_scraped TEXT NOT NULL,
        state_code TEXT NOT NULL,
        district_code TEXT NOT NULL,
        court_code TEXT NOT NULL,
        establishment_code TEXT,
        act_code TEXT NOT NULL,
        act_name TEXT NOT NULL
    )
    """
    try:
        cursor = connection.cursor()
        cursor.execute(create_table_sql)
        connection.commit()
        print("Table 'Acts' created successfully.")
    except Error as e:
        print(f"Error creating table: {e}")


# Function to save to the HTML storage table
def save_codes_to_db(
    connection,
    date_scraped,
    state_code,
    district_code,
    court_code,
    court_name,
    establishment_code,
    establishment_name,
):
    insert_sql = """
    INSERT INTO Courts (date_scraped, state_code, district_code, court_code, court_name, establishment_code, establishment_name)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    try:
        cursor = connection.cursor()
        cursor.execute(
            insert_sql,
            (
                date_scraped,
                state_code,
                district_code,
                court_code,
                court_name,
                establishment_code,
                establishment_name,
            ),
        )
        connection.commit()
        print(f"Court details saved successfully.")
    except Error as e:
        print(f"Error saving Court details to database: {e}")


# Function to save to the HTML storage table
def save_acts_to_db(
    connection,
    date_scraped,
    state_code,
    district_code,
    court_code,
    establishment_code,
    act_code,
    act_name,
):
    insert_sql = """
    INSERT INTO Acts (date_scraped, state_code, district_code, court_code, establishment_code, act_code, act_name)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    try:
        cursor = connection.cursor()
        cursor.execute(
            insert_sql,
            (
                date_scraped,
                state_code,
                district_code,
                court_code,
                establishment_code,
                act_code,
                act_name,
            ),
        )
        connection.commit()
        print(f"Act details saved successfully.")
    except Error as e:
        print(f"Error saving Court details to database: {e}")


# Function to insert data into the table
def insert_data(connection, insert_sql):
    print("We are here in db2.py")
    try:
        cursor = connection.cursor()
        cursor.execute(insert_sql)
        connection.commit()
        print(f"Data inserted successfully.")
    except Error as e:
        print(f"Error inserting data: {e}")


# Function to query data from the table
def query_table(connection):
    query_sql = "SELECT * FROM States"
    try:
        cursor = connection.cursor()
        cursor.execute(query_sql)
        rows = cursor.fetchall()
        for row in rows:
            print(row)
    except Error as e:
        print(f"Error querying table: {e}")


# Function to fetch the first 2 rows from the Districts table
def fetch_first_two_rows(connection):
    query_sql = "SELECT * FROM Districts"
    try:
        cursor = connection.cursor()
        cursor.execute(query_sql)
        rows = cursor.fetchall()
        return rows
    except Error as e:
        print(f"Error fetching rows: {e}")
        return None


# Function to fetch the first 2 rows from the Courts table
def fetch_court_rows(connection):
    query_sql = "SELECT * FROM Courts"
    try:
        cursor = connection.cursor()
        cursor.execute(query_sql)
        rows = cursor.fetchall()
        return rows
    except Error as e:
        print(f"Error fetching rows: {e}")
        return None


# Function to fetch the first 2 rows from the Acts table
def fetch_acts_rows(connection):
    query_sql = "SELECT * FROM Acts"
    try:
        cursor = connection.cursor()
        cursor.execute(query_sql)
        rows = cursor.fetchall()
        return rows
    except Error as e:
        print(f"Error fetching rows: {e}")
        return None


def custom_query(connection, query_sql):
    try:
        cursor = connection.cursor()
        cursor.execute(query_sql)
        rows = cursor.fetchall()
        return rows
    except Error as e:
        print(f"Error querying table: {e}")


# Function to drop a table from the SQLite database
def drop_table(connection, table_name):
    drop_table_sql = f"DROP TABLE IF EXISTS {table_name}"
    try:
        cursor = connection.cursor()
        cursor.execute(drop_table_sql)
        connection.commit()
        print(f"Table '{table_name}' dropped successfully.")
    except Error as e:
        print(f"Error dropping table '{table_name}': {e}")


def fetch_court_pages(connection):
    query_sql = "SELECT * FROM COURTS_HTML"
    try:
        cursor = connection.cursor()
        cursor.execute(query_sql)
        rows = cursor.fetchall()
        return rows
    except Error as e:
        print(f"Error querying table: {e}")
        return None


def add_column(connection, table_name, column_name, column_type, default_value):
    add_column_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type} DEFAULT {default_value}"
    try:
        cursor = connection.cursor()
        cursor.execute(add_column_sql)
        connection.commit()
        print(f"Column '{column_name}' added successfully.")
    except Error as e:
        print(f"Error adding column '{column_name}': {e}")


def main():
    # Step 1: Create a connection to the local SQLite database
    db_file = "jd-master-db.db"
    connection = create_connection(db_file)
    if not connection:
        return

    # # Step 2: Create a table
    # create_table(connection)

    # # Step 3: Insert data into the table
    # insert_data(connection, "New York", "NY")
    # # insert_data(connection, "California", "CA")

    # # Step 4: Query data from the table
    # query_table(connection)

    # add_column(connection, "COURTS_HTML", "section_number", "TEXT", "302")

    # Close the connection
    if connection:
        connection.close()


if __name__ == "__main__":
    main()
