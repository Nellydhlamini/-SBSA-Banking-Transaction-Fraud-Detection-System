"""
Fraud Detection System - UI (Streamlit).

Drives the real system: submitting a transaction runs it through the processor,
which persists everything to SQL Server via SqlRepository. Tabs show the stored
transactions, alerts and audit trail.

Run (after creating the schema):
    python -m streamlit run ui.py
"""
import pandas as pd
import streamlit as st
import pyodbc

from fraud_system.factory import build_processor
from fraud_system.models import Account, Customer
from fraud_system.sql_repository import SqlRepository, DB_SERVER, DB_NAME

st.set_page_config(page_title="Fraud Detection System", layout="wide")
st.title("Real-Time Fraud Detection System")
st.caption(f"Persisting to {DB_SERVER} / {DB_NAME} (schema: fds)")


@st.cache_resource
def get_system():
    repo = SqlRepository()
    processor, audit = build_processor(repo)
    return repo, processor, audit


try:
    repo, processor, audit = get_system()
except pyodbc.Error as e:
    st.error("Cannot connect to the FraudDetection database.")
    st.code(str(e))
    st.info("Check SQL Server is running and that database/schema_sqlserver.sql has been applied.")
    st.stop()


def df(records):
    rows = []
    for r in records:
        d = {}
        for k, v in vars(r).items():
            d[k] = v.value if hasattr(v, "value") else v   # enum -> its value
        rows.append(d)
    return pd.DataFrame(rows)


# ---- sidebar: accounts / seed ---------------------------------------------
accounts = repo.list_accounts()
st.sidebar.header("Accounts")
if not accounts:
    st.sidebar.warning("No accounts yet.")
    if st.sidebar.button("Create demo customer + account"):
        c = repo.add_customer(Customer(0, "Thabo Nkosi", home_country="ZA"))
        repo.add_account(Account(0, c.customer_id, "1001234567", balance=15000.0))
        st.rerun()
else:
    for a in accounts:
        st.sidebar.write(f"**{a.account_number}** - bal {a.balance:.2f} {a.currency}")

# ---- submit a transaction --------------------------------------------------
st.subheader("Submit a transaction")
if accounts:
    with st.form("submit_txn"):
        col1, col2, col3 = st.columns(3)
        acct = col1.selectbox("Account", accounts,
                              format_func=lambda a: f"{a.account_number} (bal {a.balance:.0f})")
        amount = col2.number_input("Amount", min_value=0.01, value=250.0, step=50.0)
        channel = col3.selectbox("Channel", ["POS", "ONLINE", "ATM", "EFT", "MOBILE"])
        country = col1.text_input("Country (ISO-2)", "ZA")
        submitted = st.form_submit_button("Process transaction")

    if submitted:
        result = processor.ingest(acct.account_id, amount=float(amount),
                                  channel=channel, country=country.upper().strip())
        status = result.transaction.status.value
        score = result.evaluation.risk_score if result.evaluation else "n/a"
        alerts = ", ".join(al.rule_name for al in result.alerts) or "none"
        box = {"BLOCKED": st.error, "DECLINED": st.warning, "HELD": st.warning}.get(status, st.success)
        box(f"{status} - risk score {score} - {result.message}  |  alerts: {alerts}")
        st.rerun()
else:
    st.info("Create a demo account in the sidebar to begin.")

# ---- views -----------------------------------------------------------------
t1, t2, t3 = st.tabs(["Transactions", "Open alerts", "Audit trail"])
with t1:
    st.dataframe(df(repo.list_transactions()), use_container_width=True, hide_index=True)
with t2:
    st.dataframe(df(repo.list_alerts("OPEN")), use_container_width=True, hide_index=True)
with t3:
    st.caption(f"Chain intact: {audit.verify_chain()}")
    st.dataframe(df(audit.search()), use_container_width=True, hide_index=True)
