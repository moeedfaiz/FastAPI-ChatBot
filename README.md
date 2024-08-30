FastAPI Chat Application Setup Guide
Prerequisites:
Python 3.8 or higher
MySQL Server
pip (Python package installer)
Database Setup:
Start MySQL Server: Ensure that your MySQL server is running.
Create a Database:
Log into your MySQL shell.
Execute the following SQL command to create a new database:
sql
CREATE DATABASE gainzai;
Environment Setup:
Clone the Repository: Download the code to your local machine.
git clone <repository-url>
cd fastapi-chatbot
Create and Activate a Virtual Environment:
For Windows:
python -m venv venv
.\venv\Scripts\activate
Install Dependencies: Install all required Python packages.
pip install -r requirements.txt
Configuration:
Environment Variables:
Copy the provided .env.txt file to a new .env file.
cp .env.txt .env
Open the .env file and update it with your MySQL credentials and any other required settings.
then Run your the Application(main.py)
