import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import numpy as np
import math

st.set_page_config(page_title="💰 Budget & Investment Planner", layout="wide")
st.markdown("# 💰 Personal Budget & Investment Planner")

# ===== Budget Allocator =====
st.header("📊 Budget Allocator")

with st.container():
    income = st.number_input("### 🧾 Monthly Take-home Income ($)", min_value=0.0, value=4800.0, step=100.0)

    mode = st.radio("Choose input mode:", ["Percentage (%)", "Absolute ($)"], horizontal=True)

    if mode == "Percentage (%)":
        st.markdown("### 🎯 Enter the percentage for each category")
        col1, col2, col3 = st.columns(3)
        with col1:
            needs_pct = st.slider("Needs (%)", 0, 100, 50)
        with col2:
            wants_pct = st.slider("Wants (%)", 0, 100, 30)
        with col3:
            savings_pct = st.slider("Savings (%)", 0, 100, 20)

        total_pct = needs_pct + wants_pct + savings_pct
        if total_pct != 100:
            st.warning(f"⚠️ Your percentages add up to {total_pct}%. Recommended: 100%")

        # Calculate dollar amounts
        needs_amount = income * needs_pct / 100
        wants_amount = income * wants_pct / 100
        savings_amount = income * savings_pct / 100

    else:  # Absolute mode
        st.markdown("### 💡 Enter how much you want to allocate to each category:")

        # Defaults from 50/30/20
        default_needs = round(income * 0.5, 2)
        default_wants = round(income * 0.3, 2)
        default_savings = round(income * 0.2, 2)

        col1, col2, col3 = st.columns(3)
        with col1:
            needs_amount = st.number_input("Needs ($)", min_value=0.0, value=default_needs, step=100.0, key="needs_input")
        with col2:
            wants_amount = st.number_input("Wants ($)", min_value=0.0, value=default_wants, step=100.0, key="wants_input")
        with col3:
            savings_amount = st.number_input("Savings ($)", min_value=0.0, value=default_savings, step=100.0, key="savings_input")

        total_allocated = needs_amount + wants_amount + savings_amount

        if total_allocated > income:
            st.error(f"⚠️ You've allocated ${total_allocated:,.2f}, which exceeds your income of ${income:,.2f}.")
        elif total_allocated < income:
            st.info(f"ℹ️ You've allocated ${total_allocated:,.2f} — ${income - total_allocated:,.2f} unallocated.")
        else:
            st.success("✅ Perfect! Everything is allocated.")

        def percent(amount): return (amount / income * 100) if income > 0 else 0
        needs_pct = percent(needs_amount)
        wants_pct = percent(wants_amount)
        savings_pct = percent(savings_amount)

    # Budget DataFrame
    budget_data = [
        {"Category": "Needs", "Amount": needs_amount, "Percent": needs_pct, "Color": "#0088FE"},
        {"Category": "Wants", "Amount": wants_amount, "Percent": wants_pct, "Color": "#00C49F"},
        {"Category": "Savings", "Amount": savings_amount, "Percent": savings_pct, "Color": "#FFBB28"},
    ]
    budget_df = pd.DataFrame(budget_data)

    # Interactive Pie Chart with Plotly
    chart_col, table_col = st.columns([1, 2])
    with chart_col:
        st.markdown("#### 🥧 Allocation Pie Chart (Hover for details)")

        fig = px.pie(
            budget_df,
            values='Amount',
            names='Category',
            color='Category',
            color_discrete_map={row["Category"]: row["Color"] for _, row in budget_df.iterrows()},
            hole=0.4,
        )
        fig.update_traces(textinfo='percent+label', textposition='inside', textfont_size=12)
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300, width=300, paper_bgcolor='rgba(0,0,0,0)')
        st.plotly_chart(fig, use_container_width=True)

    with table_col:
        st.markdown("#### 💸 Budget Breakdown")
        st.dataframe(
            budget_df[["Category", "Amount", "Percent"]].style.format({
                "Amount": "${:,.2f}",
                "Percent": "{:.1f}%",
            }),
            use_container_width=True
        )

    # ===== Savings Goal Tracker =====
    st.header("🎯 Savings Goal Tracker")

    col1, col2 = st.columns(2)

    with col1:
        st.write("Enter three of the following four values. Leave one empty or zero to calculate it.")
        starting_amount = st.number_input("Starting amount ($)", min_value=0.0, value=5000.0, step=100.0)
        monthly_savings = st.number_input("Monthly savings contribution ($)", min_value=0.0, value=500.0, step=50.0)

    with col2:
        savings_target = st.number_input("Savings target goal ($)", min_value=0.0, value=20000.0, step=500.0)
        duration_months = st.number_input("Duration (months)", min_value=0, value=0, step=1, help="Set 0 if unknown")

    rate_annual = st.number_input("Estimated annual interest rate (%)", min_value=0.0, value=3.0, step=0.1) / 100
    compounding_freq = st.selectbox("Compounding frequency", ["Annually", "Monthly", "Quarterly"], index=1)

    freq_map = {"Annually": 1, "Quarterly": 4, "Monthly": 12}
    n = freq_map[compounding_freq]

    # Helper: Effective monthly rate for compound interest calculation
    monthly_rate = (1 + rate_annual / n) ** (n / 12) - 1 if rate_annual > 0 else 0

    def calculate_duration(start, monthly, target, r):
        if monthly == 0 and start >= target:
            return 0
        if r == 0:
            # Simple math if no interest
            if monthly == 0:
                return math.inf  # never reach target
            return max(0, math.ceil((target - start) / monthly))
        # Use formula for number of months:
        try:
            numerator = math.log((monthly + r * target) / (monthly + r * start))
            denominator = math.log(1 + r)
            return math.ceil(numerator / denominator)
        except:
            return math.inf

    def calculate_monthly(start, target, duration, r):
        if duration == 0:
            return 0
        if r == 0:
            return max(0, (target - start) / duration)
        numerator = target - start * ((1 + r) ** duration)
        denominator = ((1 + r) ** duration - 1) / r
        return numerator / denominator if denominator != 0 else 0

    def calculate_start(target, monthly, duration, r):
        if duration == 0:
            return 0
        if r == 0:
            return target - monthly * duration
        return (target - monthly * (((1 + r) ** duration - 1) / r)) / ((1 + r) ** duration)

    def calculate_target(start, monthly, duration, r):
        if duration == 0:
            return start
        if r == 0:
            return start + monthly * duration
        return start * ((1 + r) ** duration) + monthly * (((1 + r) ** duration - 1) / r)

    # Determine which value to calculate (the one that is zero or not given)
    # Priority: duration -> monthly_savings -> starting_amount -> savings_target
    calculated_value = None

    if duration_months == 0:
        # Calculate duration
        duration_months = calculate_duration(starting_amount, monthly_savings, savings_target, monthly_rate)
        calculated_value = "Duration (months)"
    elif monthly_savings == 0:
        # Calculate monthly savings needed
        monthly_savings = calculate_monthly(starting_amount, savings_target, duration_months, monthly_rate)
        calculated_value = "Monthly savings ($)"
    elif starting_amount == 0:
        # Calculate starting amount needed
        starting_amount = calculate_start(savings_target, monthly_savings, duration_months, monthly_rate)
        calculated_value = "Starting amount ($)"
    elif savings_target == 0:
        # Calculate target savings
        savings_target = calculate_target(starting_amount, monthly_savings, duration_months, monthly_rate)
        calculated_value = "Savings target goal ($)"
    else:
        calculated_value = None  # All filled

    # Show calculated results
    st.write("---")
    st.write("### Savings Plan Summary")
    st.write(f"Starting Amount: ${starting_amount:,.2f}")
    st.write(f"Monthly Savings: ${monthly_savings:,.2f}")
    st.write(f"Duration: {duration_months} months ({duration_months / 12:.1f} years)")
    st.write(f"Savings Target: ${savings_target:,.2f}")

    if calculated_value:
        st.info(f"Calculated **{calculated_value}** based on the inputs.")

    # Visualize growth over time
    months = int(duration_months)
    balances = []
    balance = starting_amount
    for m in range(months + 1):
        if m == 0:
            balances.append(balance)
        else:
            # Apply interest monthly then add monthly savings
            balance = balance * (1 + monthly_rate) + monthly_savings
            balances.append(balance)

    growth_df = pd.DataFrame({"Month": list(range(months + 1)), "Balance": balances})

    st.line_chart(growth_df.set_index("Month")["Balance"])

# ===== Investment Calculator =====
st.header("📈 Investment Growth Calculator")

with st.container():
    col1, col2 = st.columns(2)
    with col1:
        start_amt = st.number_input("Starting amount ($)", min_value=0.0, value=20000.0, step=500.0)
        contribution = st.number_input("Monthly contribution ($)", min_value=0.0, value=1000.0, step=100.0)
    with col2:
        years = st.number_input("Years to invest", min_value=1, value=10)

        compounding_freq = st.selectbox(
            "Compounding frequency",
            options=["Annually", "Quarterly", "Monthly"],
            index=0,
        )
        rate = st.number_input("Annual return rate (%)", min_value=0.0, value=7.0, step=0.1) / 100

    # Map frequency to number of compounds per year
    freq_map = {"Annually": 1, "Quarterly": 4, "Monthly": 12}
    n = freq_map[compounding_freq]

    # Investment calculation with compounding frequency
    balance = start_amt
    total_invested = start_amt
    investment_summary = []

    for year in range(years + 1):
        if year == 0:
            investment_summary.append([0, 0.0, 0.0, balance])
        else:
            invest = contribution * 12
            total_invested += invest
            balance += invest
            # Compound interest formula for periodic compounding inside the year:
            interest = balance * ((1 + rate / n) ** n - 1)
            balance += interest
            investment_summary.append([year, invest, interest, balance])

    # Create dataframe for display
    summary_df = pd.DataFrame(investment_summary, columns=["Year", "Investment", "Earnings", "Balance"])
    summary_df = summary_df.astype({"Year": int, "Investment": float, "Earnings": float, "Balance": float})

    # Results Summary
    st.subheader("📋 Results Summary")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Amount Invested", f"${total_invested:,.2f}")
    with col2:
        st.metric("Ending Balance", f"${balance:,.2f}")

    st.subheader("📅 Yearly Investment Breakdown")
    st.dataframe(
        summary_df.style.format({
            "Investment": "${:,.2f}",
            "Earnings": "${:,.2f}",
            "Balance": "${:,.2f}"
        }),
        use_container_width=True
    )
