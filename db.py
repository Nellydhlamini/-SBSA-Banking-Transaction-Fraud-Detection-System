"""Database connection for the RTPFDS dashboard (SQL Server via pyodbc)."""
import pyodbc

DB_DRIVER   = "ODBC Driver 18 for SQL Server"
DB_SERVER   = r"localhost\SQLEXPRESS"
DB_NAME     = "FraudDetection"
DB_USER     = ""          # blank = Windows Authentication
DB_PASSWORD = ""


def connection_string() -> str:
    base = (f"DRIVER={{{DB_DRIVER}}};SERVER={DB_SERVER};DATABASE={DB_NAME};"
            f"Encrypt=yes;TrustServerCertificate=yes;")
    if DB_USER:
        return base + f"UID={DB_USER};PWD={DB_PASSWORD};"
    return base + "Trusted_Connection=yes;"


def get_connection() -> pyodbc.Connection:
    return pyodbc.connect(connection_string())
