import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# ------------------------------
# Page Config
# ------------------------------
st.set_page_config(
    page_title="Personal Finance Dashboard", 
    layout="wide", 
    initial_sidebar_state="expanded",
    page_icon="💰"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1e3d59;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stMetric {
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------
# Helper Functions
# ------------------------------
@st.cache_data
def load_sample_data():
    """Load sample data for demonstration"""
    sample_data = pd.DataFrame([
        ["2024-01-01", 50000, "Salary", "Monthly salary"],
        ["2024-01-02", -5000, "Food", "Groceries"],
        ["2024-01-03", -15000, "Bills", "Electricity and water"],
        ["2024-01-05", -3000, "Transport", "Fuel"],
        ["2024-01-10", -8000, "Shopping", "Clothes"],
        ["2024-01-15", 5000, "Other", "Freelance work"],
        ["2024-02-01", 52000, "Salary", "Monthly salary with bonus"],
        ["2024-02-03", -6000, "Food", "Groceries and dining"],
        ["2024-02-05", -12000, "Bills", "Rent and utilities"],
    ], columns=["Date", "Amount", "Category", "Description"])
    sample_data["Date"] = pd.to_datetime(sample_data["Date"])
    return sample_data

def calculate_financial_health_score(df):
    """Calculate a financial health score based on various factors"""
    if df.empty:
        return 0
    
    # Calculate metrics
    total_income = df[df["Amount"] > 0]["Amount"].sum()
    total_expenses = -df[df["Amount"] < 0]["Amount"].sum()
    savings_rate = (total_income - total_expenses) / total_income if total_income > 0 else 0
    
    # Calculate expense diversity (lower is better)
    expense_categories = df[df["Amount"] < 0]["Category"].nunique()
    expense_diversity = min(expense_categories / 5, 1)  # Normalize to 5 categories
    
    # Calculate consistency (coefficient of variation of expenses)
    monthly_expenses = df[df["Amount"] < 0].groupby(df["Date"].dt.to_period("M"))["Amount"].sum()
    expense_consistency = 1 - (monthly_expenses.std() / abs(monthly_expenses.mean())) if len(monthly_expenses) > 1 else 1
    expense_consistency = max(0, min(expense_consistency, 1))
    
    # Weighted score
    score = (savings_rate * 0.5 + expense_consistency * 0.3 + expense_diversity * 0.2) * 100
    return max(0, min(score, 100))

def get_spending_insights(df):
    """Generate spending insights and recommendations"""
    insights = []
    
    if df.empty:
        return ["Add some transactions to get personalized insights!"]
    
    # Spending by category analysis
    expense_df = df[df["Amount"] < 0].copy()
    if not expense_df.empty:
        expense_df["Amount"] = -expense_df["Amount"]
        category_spending = expense_df.groupby("Category")["Amount"].sum().sort_values(ascending=False)
        
        highest_category = category_spending.index[0]
        highest_amount = category_spending.iloc[0]
        total_expenses = category_spending.sum()
        
        percentage = (highest_amount / total_expenses) * 100
        insights.append(f"💡 Your highest spending category is '{highest_category}' (₹{highest_amount:,.0f} - {percentage:.1f}% of total expenses)")
        
        if percentage > 40:
            insights.append(f"⚠️ Consider reducing expenses in '{highest_category}' as it represents a large portion of your spending")
    
    # Savings rate analysis
    total_income = df[df["Amount"] > 0]["Amount"].sum()
    total_expenses = -df[df["Amount"] < 0]["Amount"].sum()
    
    if total_income > 0:
        savings_rate = ((total_income - total_expenses) / total_income) * 100
        if savings_rate >= 20:
            insights.append(f"🎉 Excellent! You're saving {savings_rate:.1f}% of your income")
        elif savings_rate >= 10:
            insights.append(f"👍 Good job! You're saving {savings_rate:.1f}% of your income")
        elif savings_rate > 0:
            insights.append(f"📈 You're saving {savings_rate:.1f}%. Try to increase it to at least 10%")
        else:
            insights.append("🚨 You're spending more than you earn! Review your expenses immediately")
    
    return insights

# ------------------------------
# Initialize Session State
# ------------------------------
if "df" not in st.session_state:
    # Option to load sample data
    st.session_state.df = pd.DataFrame(columns=["Date", "Amount", "Category", "Description"])
    st.session_state.show_sample = False

if "budgets" not in st.session_state:
    st.session_state.budgets = {
        "Food": 10000,
        "Shopping": 5000,
        "Transport": 3000,
        "Bills": 15000,
        "Other": 5000
    }

# ------------------------------
# Header
# ------------------------------
st.markdown('<h1 class="main-header">💰 Personal Finance Dashboard</h1>', unsafe_allow_html=True)
st.markdown("### Track, analyze, and optimize your financial health with advanced insights")

# ------------------------------
# Sidebar for Navigation and Filters
# ------------------------------
st.sidebar.title("🔧 Dashboard Controls")

# Navigation
page = st.sidebar.selectbox(
    "Navigate to:",
    ["📊 Dashboard", "➕ Add Transaction", "💳 Budget Manager", "📈 Analytics", "⚙️ Settings"]
)

# Sample data loader
if st.sidebar.button("📂 Load Sample Data"):
    st.session_state.df = load_sample_data()
    st.sidebar.success("Sample data loaded!")

# Data management
if st.sidebar.button("🗑️ Clear All Data"):
    st.session_state.df = pd.DataFrame(columns=["Date", "Amount", "Category", "Description"])
    st.sidebar.success("All data cleared!")

# Export data
if not st.session_state.df.empty:
    csv = st.session_state.df.to_csv(index=False)
    st.sidebar.download_button(
        label="💾 Download Data as CSV",
        data=csv,
        file_name=f"finance_data_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv"
    )

# ------------------------------
# Page Content Based on Navigation
# ------------------------------

if page == "➕ Add Transaction":
    st.subheader("➕ Add New Transaction")
    
    with st.form("transaction_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            date = st.date_input("Date", value=datetime.now())
            amount = st.number_input(
                "Amount (use negative for expenses)", 
                step=100.0, 
                value=0.0,
                help="Enter positive values for income, negative for expenses"
            )
        
        with col2:
            category = st.selectbox(
                "Category", 
                ["Salary", "Food", "Shopping", "Transport", "Bills", "Investment", "Healthcare", "Entertainment", "Other"]
            )
            description = st.text_input("Description", placeholder="Brief description of the transaction")
        
        submitted = st.form_submit_button("💾 Add Transaction", use_container_width=True)
    
    if submitted and amount != 0:
        new_data = pd.DataFrame([[date, amount, category, description]],
                                columns=["Date", "Amount", "Category", "Description"])
        st.session_state.df = pd.concat([st.session_state.df, new_data], ignore_index=True)
        st.success("✅ Transaction added successfully!")
        st.balloons()
    elif submitted and amount == 0:
        st.warning("⚠️ Please enter a non-zero amount")

elif page == "💳 Budget Manager":
    st.subheader("💳 Budget Manager")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Set Monthly Budgets")
        for category in ["Food", "Shopping", "Transport", "Bills", "Entertainment", "Healthcare", "Other"]:
            st.session_state.budgets[category] = st.number_input(
                f"{category} Budget (₹)", 
                min_value=0, 
                value=st.session_state.budgets.get(category, 5000),
                step=500,
                key=f"budget_{category}"
            )
    
    with col2:
        st.write("### Budget vs Actual (Current Month)")
        
        if not st.session_state.df.empty:
            df = st.session_state.df.copy()
            df["Date"] = pd.to_datetime(df["Date"])
            current_month = datetime.now().strftime("%Y-%m")
            monthly_data = df[df["Date"].dt.strftime("%Y-%m") == current_month]
            
            expense_data = monthly_data[monthly_data["Amount"] < 0]
            if not expense_data.empty:
                actual_spending = expense_data.groupby("Category")["Amount"].sum().abs()
                
                budget_comparison = []
                for category, budget in st.session_state.budgets.items():
                    actual = actual_spending.get(category, 0)
                    budget_comparison.append({
                        "Category": category,
                        "Budget": budget,
                        "Actual": actual,
                        "Remaining": budget - actual,
                        "Usage %": (actual / budget * 100) if budget > 0 else 0
                    })
                
                budget_df = pd.DataFrame(budget_comparison)
                
                for _, row in budget_df.iterrows():
                    usage_pct = row["Usage %"]
                    if usage_pct > 100:
                        st.error(f"🚨 {row['Category']}: ₹{row['Actual']:,.0f} (Over budget by ₹{-row['Remaining']:,.0f})")
                    elif usage_pct > 80:
                        st.warning(f"⚠️ {row['Category']}: ₹{row['Actual']:,.0f} ({usage_pct:.0f}% of budget)")
                    else:
                        st.success(f"✅ {row['Category']}: ₹{row['Actual']:,.0f} ({usage_pct:.0f}% of budget)")

elif page == "📈 Analytics":
    st.subheader("📈 Advanced Analytics")
    
    if not st.session_state.df.empty:
        df = st.session_state.df.copy()
        df["Date"] = pd.to_datetime(df["Date"])
        
        # Financial Health Score
        health_score = calculate_financial_health_score(df)
        
        col1, col2, col3 = st.columns(3)
        with col2:
            fig_gauge = go.Figure(go.Indicator(
                mode = "gauge+number+delta",
                value = health_score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Financial Health Score"},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, 50], 'color': "lightgray"},
                        {'range': [50, 80], 'color': "yellow"},
                        {'range': [80, 100], 'color': "green"}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 90
                    }
                }
            ))
            fig_gauge.update_layout(height=300)
            st.plotly_chart(fig_gauge, use_container_width=True)
        
        # Spending Insights
        st.subheader("💡 Smart Insights")
        insights = get_spending_insights(df)
        for insight in insights:
            if "🚨" in insight or "⚠️" in insight:
                st.warning(insight)
            elif "🎉" in insight or "✅" in insight:
                st.success(insight)
            else:
                st.info(insight)
        
        # Advanced Charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Daily balance trend
            df_sorted = df.sort_values("Date")
            df_sorted["Cumulative"] = df_sorted["Amount"].cumsum()
            fig_balance = px.line(
                df_sorted, 
                x="Date", 
                y="Cumulative", 
                title="💰 Account Balance Trend",
                labels={"Cumulative": "Balance (₹)"}
            )
            fig_balance.update_traces(line_color='#2E86C1')
            st.plotly_chart(fig_balance, use_container_width=True)
        
        with col2:
            # Income vs Expenses by month
            df["Month"] = df["Date"].dt.to_period("M").astype(str)
            income_monthly = df[df["Amount"] > 0].groupby("Month")["Amount"].sum()
            expense_monthly = -df[df["Amount"] < 0].groupby("Month")["Amount"].sum()
            
            monthly_comparison = pd.DataFrame({
                "Month": income_monthly.index,
                "Income": income_monthly.values,
                "Expenses": expense_monthly.reindex(income_monthly.index, fill_value=0).values
            })
            
            fig_comparison = go.Figure()
            fig_comparison.add_trace(go.Bar(name='Income', x=monthly_comparison["Month"], y=monthly_comparison["Income"], marker_color='green'))
            fig_comparison.add_trace(go.Bar(name='Expenses', x=monthly_comparison["Month"], y=monthly_comparison["Expenses"], marker_color='red'))
            fig_comparison.update_layout(title="📊 Monthly Income vs Expenses", barmode='group')
            st.plotly_chart(fig_comparison, use_container_width=True)
    else:
        st.info("Add some transactions to view analytics!")

elif page == "⚙️ Settings":
    st.subheader("⚙️ Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Data Management")
        
        # Upload CSV
        uploaded_file = st.file_uploader("📂 Upload CSV File", type=['csv'])
        if uploaded_file is not None:
            try:
                uploaded_df = pd.read_csv(uploaded_file)
                if st.button("Import Data"):
                    st.session_state.df = uploaded_df
                    st.success("Data imported successfully!")
            except Exception as e:
                st.error(f"Error reading file: {e}")
        
        # Data validation and cleanup
        if st.button("🔧 Clean Data"):
            # Remove duplicates and sort
            st.session_state.df = st.session_state.df.drop_duplicates().sort_values("Date")
            st.success("Data cleaned!")
    
    with col2:
        st.write("### Display Settings")
        
        # Currency selection (for future enhancement)
        currency = st.selectbox("Currency Symbol", ["₹", "$", "€", "£"])
        
        # Date format
        date_format = st.selectbox("Date Format", ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"])
        
        # Theme selection (placeholder for future enhancement)
        theme = st.selectbox("Dashboard Theme", ["Default", "Dark", "Light"])

else:  # Dashboard page
    df = st.session_state.df.copy()
    
    if not df.empty:
        # Convert Date to datetime
        df["Date"] = pd.to_datetime(df["Date"])
        df["Month"] = df["Date"].dt.to_period("M").astype(str)
        
        # Sidebar Filters
        st.sidebar.header("🔍 Filters")
        
        # Date range filter
        min_date = df["Date"].min().date()
        max_date = df["Date"].max().date()
        date_range = st.sidebar.date_input(
            "Date Range",
            value=(min_date, max_date),
            min_value=min_date,
            max_value=max_date
        )
        
        if len(date_range) == 2:
            start_date, end_date = date_range
            df = df[(df["Date"].dt.date >= start_date) & (df["Date"].dt.date <= end_date)]
        
        month_filter = st.sidebar.multiselect("Select Month(s)", df["Month"].unique(), default=df["Month"].unique())
        category_filter = st.sidebar.multiselect("Select Category", df["Category"].unique(), default=df["Category"].unique())
        
        df_filtered = df[(df["Month"].isin(month_filter)) & (df["Category"].isin(category_filter))]
        
        # Summary Statistics
        total_income = df_filtered[df_filtered["Amount"] > 0]["Amount"].sum()
        total_expenses = -df_filtered[df_filtered["Amount"] < 0]["Amount"].sum()
        savings = total_income - total_expenses
        avg_monthly_income = df_filtered[df_filtered["Amount"] > 0].groupby("Month")["Amount"].sum().mean()
        avg_monthly_expenses = -df_filtered[df_filtered["Amount"] < 0].groupby("Month")["Amount"].sum().mean()
        
        # Display metrics in enhanced layout
        st.subheader("📊 Financial Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "💵 Total Income", 
                f"₹{total_income:,.0f}",
                delta=f"₹{avg_monthly_income:,.0f}/month" if not pd.isna(avg_monthly_income) else None
            )
        
        with col2:
            st.metric(
                "💳 Total Expenses", 
                f"₹{total_expenses:,.0f}",
                delta=f"₹{avg_monthly_expenses:,.0f}/month" if not pd.isna(avg_monthly_expenses) else None
            )
        
        with col3:
            savings_rate = (savings / total_income * 100) if total_income > 0 else 0
            st.metric(
                "💰 Net Savings", 
                f"₹{savings:,.0f}",
                delta=f"{savings_rate:.1f}% rate"
            )
        
        with col4:
            transaction_count = len(df_filtered)
            avg_transaction = df_filtered["Amount"].mean()
            st.metric(
                "📝 Transactions", 
                f"{transaction_count:,}",
                delta=f"₹{avg_transaction:,.0f} avg"
            )
        
        # Recent transactions
        st.subheader("📋 Recent Transactions")
        recent_transactions = df_filtered.sort_values("Date", ascending=False).head(10)
        
        # Format the display
        display_df = recent_transactions.copy()
        display_df["Amount"] = display_df["Amount"].apply(lambda x: f"₹{x:,.0f}")
        display_df["Date"] = display_df["Date"].dt.strftime("%Y-%m-%d")
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Charts Section
        st.subheader("📊 Visual Analytics")
        
        # First row of charts
        col1, col2 = st.columns(2)
        
        with col1:
            # Enhanced pie chart for expenses
            expense_df = df_filtered[df_filtered["Amount"] < 0].copy()
            if not expense_df.empty:
                expense_df["Amount"] = -expense_df["Amount"]
                category_expenses = expense_df.groupby("Category")["Amount"].sum().reset_index()
                
                fig_pie = px.pie(
                    category_expenses, 
                    values="Amount", 
                    names="Category", 
                    title="💳 Expense Distribution by Category",
                    color_discrete_sequence=px.colors.qualitative.Set3
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Monthly savings trend
            monthly_summary = df_filtered.groupby("Month")["Amount"].sum().reset_index()
            if len(monthly_summary) > 1:
                fig_line = px.area(
                    monthly_summary, 
                    x="Month", 
                    y="Amount", 
                    title="📈 Monthly Savings Trend",
                    color_discrete_sequence=["#2E86C1"]
                )
                fig_line.update_traces(fill='tonexty')
                st.plotly_chart(fig_line, use_container_width=True)
        
        # Goal Tracker Section
        st.subheader("🎯 Financial Goals")
        
        col1, col2 = st.columns(2)
        
        with col1:
            monthly_goal = st.number_input("Monthly Savings Goal (₹)", min_value=0, value=10000, step=1000)
            current_month_savings = df_filtered[df_filtered["Month"] == datetime.now().strftime("%Y-%m")]["Amount"].sum()
            goal_progress = (current_month_savings / monthly_goal * 100) if monthly_goal > 0 else 0
            
            st.progress(min(abs(goal_progress) / 100, 1.0))
            st.write(f"**Current Month Progress:** {goal_progress:.1f}% (₹{current_month_savings:,.0f})")
        
        with col2:
            annual_goal = st.number_input("Annual Savings Goal (₹)", min_value=0, value=120000, step=10000)
            annual_progress = (savings / annual_goal * 100) if annual_goal > 0 else 0
            
            st.progress(min(abs(annual_progress) / 100, 1.0))
            st.write(f"**Annual Progress:** {annual_progress:.1f}% (₹{savings:,.0f})")
    
    else:
        st.info("👋 Welcome! Start by adding your first transaction or loading sample data from the sidebar.")
        
        # Quick start guide
        st.subheader("🚀 Quick Start Guide")
        st.markdown("""
        1. **📂 Load Sample Data**: Click the button in the sidebar to see the dashboard in action
        2. **➕ Add Transactions**: Navigate to 'Add Transaction' to input your income and expenses
        3. **💳 Set Budgets**: Use the 'Budget Manager' to set spending limits
        4. **📈 View Analytics**: Check the 'Analytics' page for detailed insights
        5. **⚙️ Customize**: Adjust settings and import/export data as needed
        """)
        
        # Feature highlights
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("""
            ### 📊 **Smart Analytics**
            - Financial health scoring
            - Spending pattern analysis
            - Automated insights
            - Trend visualization
            """)
        
        with col2:
            st.markdown("""
            ### 💳 **Budget Tracking**
            - Category-wise budgets
            - Real-time monitoring
            - Overspending alerts
            - Usage percentage tracking
            """)
        
        with col3:
            st.markdown("""
            ### 🎯 **Goal Setting**
            - Monthly & annual goals
            - Progress tracking
            - Visual indicators
            - Achievement milestones
            """)
