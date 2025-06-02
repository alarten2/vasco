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
        
        # --- Data Cleaning and Type Conversion (moved inside the if block) ---
        df['Date'] = pd.to_datetime(df['Date'])
        # Handle potential commas in numeric columns and convert to float
        for col in ['Tank Capacity', 'Reported Stock', 'Available Storage Space', 'Avg Daily Consumption', 'Days of Supply']:
            if df[col].dtype == 'object': # Check if column is object type (string)
                df[col] = df[col].str.replace(',', '').astype(float)
            else: # Already numeric, ensure float
                df[col] = df[col].astype(float)
        
        # Filter out 'UNDOF Vehicle Registration'
        mask = df["Sector"] != "UNDOF Vehicle Registration"
        df = df[mask]

        # --- Calculations (moved inside the if block) ---
        overall_avg_daily_consumption = df["Avg Daily Consumption"].mean(skipna=True).round(1)
        last_day = df["Date"].max()
        last_5_days = last_day - timedelta(days=5)
        df_last_5_days = df[df["Date"]>= last_5_days]

        avg_consumption_last_5_days = df_last_5_days["Avg Daily Consumption"].mean().round(1)
        
        # Recalculated total_consump based on user's last request (sum of Avg Daily Consumption)
        total_consump = avg_consumption_last_5_days 
        formatted_total_consump = f"{total_consump:,.1f}"

        avg_last_5_days = df_last_5_days["Reported Stock"].sum().round(1) # Still used for % Full Capacity
        first_day_tank = df["Date"].min()
        df_first_day = df[df['Date'] == first_day_tank]
        total_tank = df_first_day["Tank Capacity"].sum()
        formatted_total_tank = f"{total_tank:,.1f}"
        formatted_avg = f"{avg_last_5_days:,.1f}"
        
        # Ensure a base for percentage if 694500 is not universally applicable or from data
        # For demonstration, keeping existing calculation for consistency with original code base
        percentage = (avg_last_5_days / df_first_day['Tank Capacity'].sum()) * 100 if df_first_day['Tank Capacity'].sum() > 0 else 0 
        vacancy_rate = 100 - percentage

        # Display Metrics
        a, b, c= st.columns((3))
        d, e, f = st.columns((3))

        a.metric(label="Tank Capacity (lts)",value=formatted_total_tank)
        b.metric(label="Avg Consumption last 5 days (lts)", value = avg_consumption_last_5_days)
        c.metric(label="Sum of Avg Daily Consumption last 5 days (lts)", value = formatted_total_consump)
        d.metric(label="Avg Stock last 5 days", value = formatted_avg)
        e.metric(label="% Full Capacity", value = f"{percentage:.2f} %")
        f.metric(label="% Vacancy Rate", value = f"{vacancy_rate:.2f} %") # Duplicate, consider removing or changing to a different metric

        # First bar chart: Total capacity per sector on the first day
        first_day = df['Date'].min()
        df_first_day = df[df['Date'] == first_day]
        capacity_by_sector = df_first_day.groupby('Sector')['Tank Capacity'].sum().reset_index()
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

        # Add a date slider at the top
        unique_dates = sorted(df['Date'].unique())
        unique_dates_dt_only = [pd.to_datetime(d).date() for d in unique_dates]

        selected_date = st.slider(
            "Select Date",
            min_value=unique_dates_dt_only[0],
            max_value=unique_dates_dt_only[-1],
            value=unique_dates_dt_only[-1],
            format="YYYY-MM-DD"
        )
        df_selected_date = df[df['Date'].dt.date == selected_date]
        unique_sectors = sorted(df['Sector'].unique())

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

        def generate_sector_plots(df_filtered_date, sector_name, color_palette_start_index):
            df_sector = df_filtered_date[df_filtered_date['Sector'] == sector_name]
            
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
                showlegend=False,
                xaxis_tickangle=-45,
                hovermode="x unified",
                height=400
            )
            return fig_sector

        st.divider()

        figures_to_display = []
        for i in range(0, len(unique_sectors)):
            sector = unique_sectors[i]
            fig = generate_sector_plots(df_selected_date, sector, i)
            if fig:
                figures_to_display.append(fig)

        for i in range(0, len(figures_to_display), 2):
            cols = st.columns(2)
            for j in range(2):
                if i + j < len(figures_to_display):
                    cols[j].plotly_chart(figures_to_display[i + j], use_container_width=True)

    except Exception as e:
        st.error(f"Error processing the uploaded file: {e}")
        st.warning("Please ensure your CSV file has the correct columns and data format.")
else:
    st.info("Please upload a CSV file to begin.")
