import bcrypt
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_USER = os.getenv("MYSQL_USER")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")
MYSQL_DB = os.getenv("MYSQL_DB")

def connect():
    """Establish a connection to the MySQL database using loaded environment variables."""
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )

def initialize_db():
    conn = connect()
    cursor = conn.cursor()
    query = """
    CREATE TABLE IF NOT EXISTS users (
        email VARCHAR(255) PRIMARY KEY,
        username VARCHAR(255),
        hashed_password VARCHAR(255)
    )
    """
    cursor.execute(query)
    conn.close()

def create_user(email, username, password):
    conn = connect()
    cursor = conn.cursor()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    query = "INSERT INTO users (email, username, hashed_password) VALUES (%s, %s, %s)"
    values = (email, username, hashed_password)
    cursor.execute(query, values)
    conn.commit()
    conn.close()

def check_user(email, password):
    conn = connect()
    cursor = conn.cursor()
    query = "SELECT hashed_password FROM users WHERE email = %s"
    cursor.execute(query, (email,))
    user = cursor.fetchone()
    conn.close()
    if user and bcrypt.checkpw(password.encode('utf-8'), user[0].encode('utf-8')):
        return True
    return False

def get_username(email):
    """Retrieve the username from the database based on the email."""
    conn = connect()
    cursor = conn.cursor()
    query = "SELECT username FROM users WHERE email = %s"
    cursor.execute(query, (email,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return user[0]  # Return the username
    return None  # Return None if no user is found