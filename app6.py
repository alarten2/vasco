import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(layout="wide")

st.title("Fuel Dashboard")

# --- File Uploader ---
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)

        # --- Data Cleaning and Type Conversion ---
        df['Date'] = pd.to_datetime(df['Date'])
        for col in ['Tank Capacity', 'Reported Stock', 'Available Storage Space', 'Avg Daily Consumption', 'Days of Supply']:
            if df[col].dtype == 'object':
                df[col] = df[col].str.replace(',', '').astype(float)
            else:
                df[col] = df[col].astype(float)

        # Filter out 'UNDOF Vehicle Registration' at the main DataFrame level
        df_filtered = df[df["Sector"] != "UNDOF Vehicle Registration"].copy()

        # --- Calculations ---
        # Overall Average Daily Consumption (using the filtered data)
        overall_avg_daily_consumption = df_filtered["Avg Daily Consumption"].mean(skipna=True).round(1)

        # Determine the last day from the filtered data
        last_day = df_filtered["Date"].max()
        last_5_days_start = last_day - timedelta(days=5)

        # Filter data for the last 5 days (using the already filtered data)
        df_last_5_days = df_filtered[df_filtered["Date"] >= last_5_days_start]

        # Corrected: Calculate the AVERAGE consumption of the last 5 days
        avg_consumption_last_5_days = df_last_5_days["Avg Daily Consumption"].mean().round(1)

        # Corrected: Calculate the TOTAL consumption of the last 5 days
        total_consumption_last_5_days = df_last_5_days["Avg Daily Consumption"].sum().round(1)
        formatted_total_consumption_last_5_days = f"{total_consumption_last_5_days:,.1f}"

        # Original calculation for Avg Stock last 5 days (used for % Full Capacity)
        avg_last_5_days_reported_stock = df_last_5_days["Reported Stock"].sum().round(1)
        formatted_avg_last_5_days_reported_stock = f"{avg_last_5_days_reported_stock:,.1f}"

        # Calculations for Tank Capacity
        first_day_tank = df_filtered["Date"].min()
        df_first_day = df_filtered[df_filtered['Date'] == first_day_tank]
        total_tank_capacity = df_first_day["Tank Capacity"].sum()
        formatted_total_tank_capacity = f"{total_tank_capacity:,.1f}"

        # Percentage calculations
        # Ensure a base for percentage if total_tank_capacity is 0 to avoid division by zero
        percentage_full_capacity = (avg_last_5_days_reported_stock / total_tank_capacity) * 100 if total_tank_capacity > 0 else 0
        vacancy_rate = 100 - percentage_full_capacity

        # Display Metrics
        a, b, c = st.columns((3))
        d, e, f = st.columns((3))

        a.metric(label="Total Tank Capacity (lts)", value=formatted_total_tank_capacity)
        b.metric(label="Avg Daily Consumption last 5 days (lts)", value=avg_consumption_last_5_days)
        c.metric(label="Total Consumption last 5 days (lts)", value=formatted_total_consumption_last_5_days)
        d.metric(label="Total Reported Stock last 5 days", value=formatted_avg_last_5_days_reported_stock)
        e.metric(label="% Full Capacity", value=f"{percentage_full_capacity:.2f} %")
        f.metric(label="% Vacancy Rate", value=f"{vacancy_rate:.2f} %")

        # First bar chart: Total capacity per sector on the first day
        # Ensure 'df_filtered' is used here to exclude UNDOF from this plot as well
        first_day = df_filtered['Date'].min() # Use df_filtered
        df_first_day_filtered = df_filtered[df_filtered['Date'] == first_day] # Use df_filtered
        capacity_by_sector = df_first_day_filtered.groupby('Sector')['Tank Capacity'].sum().reset_index() # Use df_first_day_filtered
        capacity_by_sector = capacity_by_sector.sort_values(by='Tank Capacity', ascending=False)

        gradient_colors = px.colors.sequential.Oranges[::-1][:len(capacity_by_sector)]

        fig1 = go.Figure()
        for i, row in capacity_by_sector.iterrows():
            fig1.add_trace(go.Bar(
                x=[row['Sector']],
                y=[row['Tank Capacity']],
                text=[f"{row['Tank Capacity']:.0f}"],
                textposition='auto',
                marker_color=gradient_colors[i % len(gradient_colors)],
                name=row['Sector']
            ))

        fig1.update_layout(
            title="Total Capacity per Sector (lts)",
            xaxis_title="Sector",
            yaxis_title="Tank Capacity",
            uniformtext_minsize=8,
            uniformtext_mode='show',
            showlegend=False
        )
        st.plotly_chart(fig1, use_container_width=True)

        # --- Visualizations (Consumption and Stock Trend) ---
        st.subheader("Daily Consumption Trend")
        fig_consumption = px.line(df_filtered, x='Date', y='Avg Daily Consumption', title='Average Daily Consumption Over Time')
        st.plotly_chart(fig_consumption, use_container_width=True)

        st.subheader("Reported Stock Trend")
        fig_stock = px.line(df_filtered, x='Date', y='Reported Stock', title='Reported Stock Over Time')
        st.plotly_chart(fig_stock, use_container_width=True)


        # --- Sector-specific plots ---

        # Add a date slider at the top
        unique_dates = sorted(df_filtered['Date'].unique()) # Use df_filtered here
        unique_dates_dt_only = [pd.to_datetime(d).date() for d in unique_dates]

        selected_date = st.slider(
            "Select Date",
            min_value=unique_dates_dt_only[0],
            max_value=unique_dates_dt_only[-1],
            value=unique_dates_dt_only[-1],
            format="YYYY-MM-DD"
        )
        df_selected_date = df_filtered[df_filtered['Date'].dt.date == selected_date] # Use df_filtered


        st.header("Fuel Overview")

        common_tc_color = px.colors.sequential.Viridis[3]
        common_ass_color = px.colors.sequential.Viridis[5]
        common_dos_color = 'red'

        st.markdown(
            f"""
            <div style="display: flex; flex-wrap: wrap; gap: 20px; align-items: center; margin-bottom: 20px;">
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; background-color: {common_tc_color}; margin-right: 5px;"></div>
                    <span>Tank Capacity</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; background-color: {common_ass_color}; margin-right: 5px;"></div>
                    <span>Available Storage Space</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 2px; background-color: {common_dos_color}; margin-right: 5px;"></div>
                    <span>Days of Supply</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        def generate_sector_plots(df_input, sector_name):
            df_sector = df_input[df_input['Sector'] == sector_name]

            if df_sector.empty:
                return None

            fig_sector = go.Figure()

            bar_tc_color = px.colors.sequential.Viridis[3]
            bar_ass_color = px.colors.sequential.Viridis[5]
            line_dos_color = 'red'

            fig_sector.add_trace(go.Bar(
                x=df_sector['Post'],
                y=df_sector['Tank Capacity'],
                name='Tank Capacity',
                marker_color=bar_tc_color
            ))
            fig_sector.add_trace(go.Bar(
                x=df_sector['Post'],
                y=df_sector['Available Storage Space'],
                name='Available Storage Space',
                marker_color=bar_ass_color
            ))

            fig_sector.add_trace(go.Scatter(
                x=df_sector['Post'],
                y=df_sector['Days of Supply'],
                mode='lines+markers+text',
                name='Days of Supply',
                yaxis='y2',
                line=dict(color=line_dos_color, width=2),
                text=df_sector['Days of Supply'].round(1),
                textposition='middle left'
            ))

            fig_sector.update_layout(
                title=f'{sector_name} - per Post ({selected_date.strftime("%Y-%m-%d")})',
                xaxis_title='Post',
                yaxis=dict(title='Volume (Liters)'),
                yaxis2=dict(title='Days of Supply', overlaying='y', side='right', showgrid=False),
                barmode='group',
                showlegend=True, # Changed to True to show legend for multiple traces
                xaxis_tickangle=-45,
                hovermode="x unified",
                height=400
            )
            return fig_sector

        st.divider()

        figures_to_display = []
        # Get unique sectors from the already filtered DataFrame (df_filtered)
        unique_sectors = df_filtered['Sector'].unique().tolist()

        # The 'UNDOF Vehicle Registration' will already be excluded if df_filtered was created correctly,
        # but this check ensures it for robustness if df_filtered isn't universally applied elsewhere.
        if "UNDOF Vehicle Registration" in unique_sectors:
            unique_sectors.remove("UNDOF Vehicle Registration")

        for sector in unique_sectors:
            fig = generate_sector_plots(df_selected_date, sector)
            if fig:
                figures_to_display.append(fig)

        for i in range(0, len(figures_to_display), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(figures_to_display):
                    cols[j].plotly_chart(figures_to_display[i + j], use_container_width=True)

    except Exception as e:
        st.error(f"Error processing file: {e}")
        st.info("Please ensure your CSV file has the expected columns: 'Date', 'Tank Capacity', 'Reported Stock', 'Available Storage Space', 'Avg Daily Consumption', 'Days of Supply', and 'Sector'.")
else:
    st.info("Please upload a CSV file to begin.")
