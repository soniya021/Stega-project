import sqlite3
from sqlite3 import Error

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)
    return conn

def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)

def initialize_database():
    database = "steganography.db"

    sql_create_images_table = """ CREATE TABLE IF NOT EXISTS images (
                                        id integer PRIMARY KEY,
                                        image_path text NOT NULL,
                                        hidden_message text
                                    ); """

    conn = create_connection(database)

    if conn is not None:
        create_table(conn, sql_create_images_table)
    else:
        print("Error! cannot create the database connection.")

if __name__ == '__main__':
    initialize_database()
