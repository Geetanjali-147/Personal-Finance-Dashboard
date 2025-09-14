import streamlit as st
import pandas as pd
import plotly.express as px

# ------------------------------
# Page Config
# ------------------------------
st.set_page_config(page_title="Personal Finance Dashboard", layout="wide")
st.title("💰 Personal Finance Dashboard")
st.markdown("Add your transactions manually and analyze your financial health.")

# ------------------------------
# Initialize Session State
# ------------------------------
if "df" not in st.session_state:
    st.session_state.df = pd.DataFrame(columns=["Date", "Amount", "Category", "Description"])

# ------------------------------
# Add Transaction Form
# ------------------------------
st.subheader("➕ Add Transaction")

with st.form("transaction_form"):
    date = st.date_input("Date")
    amount = st.number_input("Amount (use negative for expenses)", step=100, value=0)
    category = st.selectbox("Category", ["Salary", "Food", "Shopping", "Transport", "Bills", "Other"])
    description = st.text_input("Description")
    submitted = st.form_submit_button("Add Transaction")

if submitted:
    new_data = pd.DataFrame([[date, amount, category, description]],
                             columns=["Date", "Amount", "Category", "Description"])
    st.session_state.df = pd.concat([st.session_state.df, new_data], ignore_index=True)
    st.success("✅ Transaction added!")

# ------------------------------
# Show Data
# ------------------------------
df = st.session_state.df.copy()

if not df.empty:
    st.subheader("📋 Transactions")
    st.dataframe(df)

    # Convert Date to datetime
    df["Date"] = pd.to_datetime(df["Date"])
    df["Month"] = df["Date"].dt.to_period("M").astype(str)

    # ------------------------------
    # Sidebar Filters
    # ------------------------------
    st.sidebar.header("🔍 Filters")
    month_filter = st.sidebar.multiselect("Select Month(s)", df["Month"].unique(), default=df["Month"].unique())
    category_filter = st.sidebar.multiselect("Select Category", df["Category"].unique(), default=df["Category"].unique())

    df_filtered = df[(df["Month"].isin(month_filter)) & (df["Category"].isin(category_filter))]

    # ------------------------------
    # Summary Stats
    # ------------------------------
    total_income = df_filtered[df_filtered["Amount"] > 0]["Amount"].sum()
    total_expenses = -df_filtered[df_filtered["Amount"] < 0]["Amount"].sum()
    savings = total_income - total_expenses

    col1, col2, col3 = st.columns(3)
    col1.metric("💵 Total Income", f"₹{total_income:,.0f}")
    col2.metric("💳 Total Expenses", f"₹{total_expenses:,.0f}")
    col3.metric("💰 Savings", f"₹{savings:,.0f}")

    # ------------------------------
    # Charts
    # ------------------------------
    st.subheader("📊 Visual Insights")

    # Category-wise expenses
    expense_df = df_filtered[df_filtered["Amount"] < 0].copy()
    expense_df["Amount"] = -expense_df["Amount"]
    if not expense_df.empty:
        fig_pie = px.pie(expense_df, values="Amount", names="Category", title="Category-wise Expense Breakdown")
        st.plotly_chart(fig_pie, use_container_width=True)

    # Monthly trend
    monthly_summary = df_filtered.groupby("Month")["Amount"].sum().reset_index()
    fig_line = px.line(monthly_summary, x="Month", y="Amount", title="Monthly Net Savings Trend", markers=True)
    st.plotly_chart(fig_line, use_container_width=True)

    # ------------------------------
    # Goal Tracker
    # ------------------------------
    st.subheader("🎯 Goal Tracker")
    goal = st.number_input("Set a savings goal (₹)", min_value=0, value=5000, step=500)
    progress = (savings / goal) * 100 if goal > 0 else 0
    st.progress(min(progress / 100, 1.0))
    st.write(f"✅ Progress: {progress:.2f}%")
else:
    st.info("👉 Add transactions above to see dashboard.")