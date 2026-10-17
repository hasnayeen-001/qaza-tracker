import io
import math
import numpy as np
import pandas as pd
import streamlit as st
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, NextPageTemplate, PageBreak, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfgen import canvas

# Page Configuration
st.set_page_config(page_title="Qaza Prayer Tracker System", page_icon="🕋", layout="wide")

st.title("🕋 Automated Qaza Prayer Tracker & Printable Generator")
st.markdown("Calculate your missed prayers, adjust your **safety margin**, allocate your lifetime debts across the 5 daily prayers, and generate a **print-ready PDF**.")

# ==========================================
# STEP 1: YEAR RANGE SELECTOR & HISTORY
# ==========================================
st.header("Step 1: Select Your Year Range & Prayer History")
st.markdown("Select your starting year (e.g., year of puberty) and ending year. The system will automatically generate your yearly table. *(Tip: The years are locked automatically, but you can freely click and type into the **Adjusted Days** and **Avg Wakt** columns).*")

col_yr1, col_yr2 = st.columns(2)
start_year = col_yr1.number_input("Start Year", min_value=1950, max_value=2030, value=2017, step=1)
end_year = col_yr2.number_input("End Year", min_value=1950, max_value=2030, value=2025, step=1)

if start_year > end_year:
    st.error("⚠️ Start Year cannot be later than End Year. Please adjust your range.")
    st.stop()

# Session State to manage the dynamic year range table smoothly without resetting user edits
range_key = f"df_{start_year}_{end_year}"
if range_key not in st.session_state:
    years = list(range(int(start_year), int(end_year) + 1))
    st.session_state[range_key] = pd.DataFrame({
        "Year": years,
        "Days": [365] * len(years),
        "Avg_Wakt_Prayed": [3.5] * len(years)
    })

edited_df = st.data_editor(
    st.session_state[range_key], 
    key=f"editor_{range_key}",
    hide_index=True,
    column_config={
        "Year": st.column_config.NumberColumn("Year", disabled=True, format="%d"),
        "Days": st.column_config.NumberColumn("Adjusted Days", min_value=0, max_value=366, step=1),
        "Avg_Wakt_Prayed": st.column_config.NumberColumn("Avg Wakt Prayed (Max 5)", min_value=0.0, max_value=5.0, step=0.1)
    }
)

# Update session state with edits
st.session_state[range_key] = edited_df
cleaned_df = edited_df.fillna(0).copy()

# Calculations (5 Wakts per day fixed)
cleaned_df["Total_Wakt"] = cleaned_df["Days"].apply(lambda x: math.ceil(x * 5))
cleaned_df["Actual_Prayed"] = (cleaned_df["Days"] * cleaned_df["Avg_Wakt_Prayed"]).apply(math.ceil)
cleaned_df["Missed"] = (cleaned_df["Total_Wakt"] - cleaned_df["Actual_Prayed"]).clip(lower=0).apply(math.ceil)

total_obligatory = int(cleaned_df["Total_Wakt"].sum())
total_actual = int(cleaned_df["Actual_Prayed"].sum())
total_missed = int(cleaned_df["Missed"].sum())
num_years = len(cleaned_df)

st.divider()

# ==========================================
# STEP 2: SUMMARY & SAFETY MARGIN
# ==========================================
st.header("Step 2: Summary & Safety Margin")

col1, col2, col3 = st.columns(3)
col1.metric("Total Obligatory Prayers", f"{total_obligatory:,}")
col2.metric("Total Actual Prayed", f"{total_actual:,}")
col3.metric("Calculated Missed Prayers", f"{total_missed:,}")

default_safety_target = int(math.ceil(total_missed / 1000.0) * 1000) if total_missed > 0 else 1000

st.markdown("### Safety Margin & Manual Adjustment")
st.markdown("To ensure complete spiritual peace of mind, the system suggests rounding up your missed prayers to the nearest 1,000. You can use the manual adjustment field below if you prefer a custom target.")

overestimated_target = st.number_input(
    "Final Safety Target (Wakts)",
    min_value=0,
    value=default_safety_target,
    step=500
)

st.divider()

# ==========================================
# STEP 3: MANUAL LIFETIME ALLOCATION (5 WAKTS)
