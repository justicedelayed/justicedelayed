import os
import requests
import json
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# DigitalOcean API token from .env file
DO_API_TOKEN = os.getenv("DO_API_TOKEN")

# Headers for API requests
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {DO_API_TOKEN}",
}


# Step 1: Create a DigitalOcean Managed Database
def create_managed_database():
    url = "https://api.digitalocean.com/v2/databases"

    data = {
        "name": "jd-master-db",
        "engine": "mysql",
        "version": "8",
        "region": "nyc3",
        "size": "db-s-1vcpu-1gb",
        "num_nodes": 1,
        "tags": ["production"],
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 201:
        db_info = response.json()
        print("Managed Database created successfully.")
        return db_info
    else:
        print(f"Failed to create Managed Database: {response.text}")
        return None


# Step 2: Get Connection Details
def get_database_connection_details(database_id):
    url = f"https://api.digitalocean.com/v2/databases/{database_id}"

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        db_info = response.json()
        connection_details = db_info["database"]["connection"]
        return connection_details
    else:
        print(f"Failed to retrieve connection details: {response.text}")
        return None


# Step 3: Connect to the Managed Database and Perform Operations
def connect_to_database(connection_details):
    try:
        connection = mysql.connector.connect(
            host=connection_details["host"],
            user=connection_details["user"],
            password=connection_details["password"],
            database="defaultdb",  # Managed DBs often come with a default database
            port=connection_details["port"],
        )
        print("Connected to MySQL database.")
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


def create_table(connection):
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS States (
        id INT AUTO_INCREMENT PRIMARY KEY,
        state_name VARCHAR(100) NOT NULL,
        state_code VARCHAR(10) NOT NULL
    )
    """
    try:
        cursor = connection.cursor()
        cursor.execute(create_table_sql)
        connection.commit()
        print("Table created successfully.")
    except Error as e:
        print(f"Error creating table: {e}")


def insert_data(connection, insert_sql):
    # insert_sql = "INSERT INTO States (state_name, state_code) VALUES (%s, %s)"
    try:
        cursor = connection.cursor()
        cursor.execute(insert_sql)
        connection.commit()
        print("Data inserted successfully.")
    except Error as e:
        print(f"Error inserting data: {e}")


def display_table(connection):
    query_sql = "SELECT * FROM States"
    try:
        cursor = connection.cursor()
        cursor.execute(query_sql)
        rows = cursor.fetchall()
        for row in rows:
            print(row)
    except Error as e:
        print(f"Error querying table: {e}")


def main():
    # Step 1: Create the Managed Database
    db_info = create_managed_database()
    if not db_info:
        return

    # Extract database ID and get connection details
    database_id = db_info["database"]["id"]
    connection_details = get_database_connection_details(database_id)

    print("Connection Details:", connection_details)

    if not connection_details:
        return

    # Step 2: Connect to the Managed Database
    connection = connect_to_database(connection_details)
    if not connection:
        return

    # Step 3: Create a table
    create_table(connection)

    # # Step 4: Insert data into the table
    # insert_data(connection, "New York", "NY")
    insert_data(connection, "California", "CA")

    # Step 5: Query data from the table
    display_table(connection)

    # Close the connection
    if connection:
        connection.close()


if __name__ == "__main__":
    main()
