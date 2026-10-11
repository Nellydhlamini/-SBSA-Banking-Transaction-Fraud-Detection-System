Real-Time Transaction Processing & Fraud Detection System — Database & App
Coding deliverable for the Mindworx WIL project (Software Engineering, NQF Level 6). It contains the SQL Server database for the fraud-detection system and a basic Python application that connects to it to read and write data.

1. Tech stack
Layer	Technology
Database	Microsoft SQL Server Express (instance .\SQLEXPRESS), database FraudDetection
Access driver	ODBC Driver 18 for SQL Server
Application	Python 3.12 + pyodbc
UI	Tkinter (standard library)
Offline/demo DB	SQLite (standard-library sqlite3) — no server required
2. Repository structure
Mindworx Database Design/
├── README.md                         <- this file
│
├── Create-Tables.sql                 <- plain CREATE TABLE (15 tables)
├── DDL-Script.sql                    <- CREATE TABLE + data-definition logic (defaults, CHECK, keys)
├── Base-Constraints-ALTER.sql        <- add base-table constraints via ALTER TABLE
├── Junction-Tables.sql               <- M:N junction tables
├── Junction-Constraints-ALTER.sql    <- junction constraints via ALTER TABLE
├── FraudDetection-Full-Schema.sql    <- idempotent one-shot: base + junctions + indexes
├── Test-ForeignKeys.sql              <- referential-integrity tests
│
├── WA0202.*.sql / WA0203.*.sql / WA0204.*.sql   <- CRUD, transactions, joins, views
│
├── python-app/                       <- SQL Server application (pyodbc)
│   ├── db.py                         <- connection string / settings
│   ├── app.py                        <- read dashboard (transactions + alerts)
│   ├── seed_and_read.py              <- insert sample data, then read it back
│   ├── ui_app.py                     <- Tkinter form: input & retrieve customers
│   └── test_crud.py                  <- READ/WRITE verification test
│
└── sqlite-app/                       <- no-install fallback (SQLite)
    ├── schema.sql                    <- SQLite schema
    ├── db.py / init_db.py / app.py / ui_app.py
3. Prerequisites
SQL Server Express running (.\SQLEXPRESS) with a database named FraudDetection.
ODBC Driver 18 for SQL Server installed.
Python 3.12 with pyodbc:
pip install pyodbc
(SQLite fallback needs nothing beyond Python.)
4. Database setup
Run the scripts against FraudDetection in SSMS or with sqlcmd.

Quickest — one script builds everything (idempotent, non-destructive):

sqlcmd -S ".\SQLEXPRESS" -E -i "FraudDetection-Full-Schema.sql"
Or step by step:

sqlcmd -S ".\SQLEXPRESS" -E -i "Create-Tables.sql"
sqlcmd -S ".\SQLEXPRESS" -E -i "Base-Constraints-ALTER.sql"
sqlcmd -S ".\SQLEXPRESS" -E -i "Junction-Tables.sql"
Verify referential integrity (optional):

sqlcmd -S ".\SQLEXPRESS" -E -i "Test-ForeignKeys.sql"
5. Running the application
5.1 Configure the connection
Open python-app/db.py and confirm:

DB_DRIVER = "ODBC Driver 18 for SQL Server"
DB_SERVER = r"localhost\SQLEXPRESS"
DB_NAME   = "FraudDetection"
DB_USER   = ""      # blank = Windows Authentication; or set a SQL login
DB_PASSWORD = ""
5.2 Load sample data and read it back
cd python-app
python seed_and_read.py
5.3 Read dashboard (transactions + fraud alerts)
python app.py                # OPEN alerts
python app.py INVESTIGATING  # filter by status
5.4 User interface (input & retrieve)
python ui_app.py
A window opens with a form to add a customer (WRITE) and a searchable table to retrieve customers (READ).

5.5 Verify READ/WRITE operations
python test_crud.py          # INSERT -> SELECT -> UPDATE -> DELETE, each checked
6. No-install fallback (SQLite)
If SQL Server is unavailable (e.g. a locked-down machine), use the SQLite build — no server, no driver, no admin rights:

cd sqlite-app
python init_db.py            # creates fraud_detection.db and seeds it
python app.py                # read
python ui_app.py             # UI
7. Data model (summary)
15 tables in 3NF. Core chain: Customer → Account → Card / Transaction, with fraud flow Transaction → FraudEvaluation → FraudAlert → Case (via CaseAlert) → Notification, and an append-only AuditLog. See DDL-Script.sql for the full schema and the ERD in the design-documents folder.

8. Troubleshooting
Symptom	Cause / fix
Login failed ... Cannot open database "..." (Msg 4060/18456)	DB_NAME doesn't match the actual database. Run SELECT name FROM sys.databases; and set DB_NAME to match; ensure your login has access.
Data source name not found / driver error	ODBC Driver 18 not installed, or DB_DRIVER name wrong.
pyodbc not found	pip install pyodbc.
Invalid column name	A script references a column the table doesn't have — rebuild with FraudDetection-Full-Schema.sql.

