"""
RTPFDS - Ops Monitoring Dashboard (Streamlit).

Reads live data from the FraudDetection SQL Server database and shows
KPIs, recent transactions, open fraud alerts, and a status breakdown.

Run:
    python -m streamlit run app.py
"""
import pandas as pd
import streamlit as st
import plotly.express as px
import pyodbc

from db import get_connection, DB_SERVER, DB_NAME

st.set_page_config(page_title="RTPFDS Dashboard", layout="wide")


@st.cache_data(ttl=30)
def run_query(sql: str, params: tuple = ()):
    """Execute a query and return a DataFrame. Cached for 30s."""
    cn = get_connection()
    try:
        cur = cn.cursor()
        cur.execute(sql, params)
        cols = [d[0] for d in cur.description]
        rows = [list(r) for r in cur.fetchall()]
        return pd.DataFrame(rows, columns=cols)
    finally:
        cn.close()


def scalar(sql: str) -> int:
    df = run_query(sql)
    return int(df.iloc[0, 0]) if not df.empty else 0


st.title("Real-Time Fraud Detection — Operations Dashboard")
st.caption(f"Source: {DB_SERVER} / {DB_NAME}")

# ---- connection check ------------------------------------------------------
try:
    get_connection().close()
except pyodbc.Error as e:
    st.error("Could not connect to the database.")
    st.code(str(e))
    st.info("Check SQL Server is running, db.py settings are correct, and the "
            "ODBC Driver 18 is installed.")
    st.stop()

# ---- sidebar filter --------------------------------------------------------
alert_status = st.sidebar.selectbox(
    "Alert status", ["OPEN", "INVESTIGATING", "CLOSED", "FALSE_POSITIVE"], index=0)

# ---- KPIs ------------------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Transactions", scalar("SELECT COUNT(*) FROM dbo.[Transaction]"))
c2.metric("Blocked", scalar("SELECT COUNT(*) FROM dbo.[Transaction] WHERE Status='BLOCKED'"))
c3.metric("Open alerts", scalar("SELECT COUNT(*) FROM dbo.FraudAlert WHERE AlertStatus='OPEN'"))
c4.metric("Customers", scalar("SELECT COUNT(*) FROM dbo.Customer"))

# ---- status breakdown chart ------------------------------------------------
st.subheader("Transactions by status")
by_status = run_query("""
    SELECT Status, COUNT(*) AS Count, SUM(Amount) AS TotalAmount
    FROM dbo.[Transaction] GROUP BY Status
""")
if by_status.empty:
    st.info("No transactions yet.")
else:
    fig = px.bar(by_status, x="Status", y="Count", text="Count",
                 title=None, color="Status")
    st.plotly_chart(fig, use_container_width=True)

# ---- recent transactions ---------------------------------------------------
st.subheader("Recent transactions")
txns = run_query("""
    SELECT TOP (100)
        t.TransactionId, c.FirstName + ' ' + c.LastName AS Customer,
        a.AccountNumber, t.Amount, t.Channel, t.Status, t.CreatedAt
    FROM dbo.[Transaction] t
    JOIN dbo.Account  a ON a.AccountId  = t.AccountId
    JOIN dbo.Customer c ON c.CustomerId = a.CustomerId
    ORDER BY t.CreatedAt DESC
""")
st.dataframe(txns, use_container_width=True, hide_index=True)

# ---- fraud alerts ----------------------------------------------------------
st.subheader(f"Fraud alerts ({alert_status})")
alerts = run_query("""
    SELECT fa.AlertId, fr.RuleName, fa.AlertSeverity, fa.AlertStatus,
           t.Amount, fa.RaisedAt
    FROM dbo.FraudAlert fa
    JOIN dbo.FraudRule  fr ON fr.RuleId        = fa.RuleId
    JOIN dbo.[Transaction] t ON t.TransactionId = fa.TransactionId
    WHERE fa.AlertStatus = ?
    ORDER BY fa.RaisedAt DESC
""", (alert_status,))
st.dataframe(alerts, use_container_width=True, hide_index=True)

st.caption("Auto-refreshes every 30 seconds (cached). Reload the page for an immediate refresh.")
