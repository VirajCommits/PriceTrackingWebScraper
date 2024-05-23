# Web Scraping Application

This project is a web scraping application developed using Python, Flask, SQLAlchemy, and React. The application scrapes product data from specified websites, stores the data in a SQLite database, and provides a frontend interface to view the product information and price history.

## Key Features

- **Web Scraping**: Scrapes product data from specified websites.
- **Data Storage**: Uses SQLite to store product details and price history.
- **Backend**: Built with Flask and SQLAlchemy for API endpoints and database interactions.
- **Frontend**: Developed using React to provide a user-friendly interface.
- **Automated Data Update**: Uses subprocesses to automate the scraping process for tracked products.

## Installation

**Clone the repository**:
   ```bash
   git clone https://github.com/your-username/web-scraping-app.git
   cd web-scraping-app
```
## Backend Setup:
### Navigate to the BackEnd directory:

```bash
cd BackEnd
```
## Create a virtual environment and activate it:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
```

## Install the required Python packages:
```bash
pip install -r requirements.txt
```
## Run the Flask app:
```bash
python app.py
```
## Navigate to the FrontEnd directory:
```bash
cd ../FrontEnd
```
## Install the required npm packages:
```bash
npm install
```
## Start the React app:
```bash
npm start
```
