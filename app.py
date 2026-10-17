import io
import numpy as np
import pandas as pd
import streamlit as st
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# Page Configuration
st.set_page_config(page_title="Qaza Prayer Tracker System", page_icon="🕋", layout="wide")

st.title("🕋 Automated Qaza Prayer Tracker & Printable Generator")
st.markdown("Calculate your missed prayers, adjust your overestimation buffer, allocate your lifetime debts, and generate a **print-ready PDF with round-square checkbox grids**.")

# ==========================================
# SETTINGS & TOGGLES
# ==========================================
st.sidebar.header("⚙️ Configuration Settings")
include_witr = st.sidebar.checkbox("Include Witr Prayer (6 Wakts / Day)", value=True, help="In Hanafi jurisprudence, Witr is Wajib and made up alongside Isha.")
wakts_per_day = 6 if include_witr else 5

# ==========================================
# STEP 1: MANUAL YEARLY INPUTS
# ==========================================
st.header("Step 1: Enter Your Yearly Prayer History")
st.markdown("Add your prayer history year by year. Enter how many valid days you prayed that year and your average wakts prayed per day.")

# Default data matching user example
default_data = pd.DataFrame({
    "Year": [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
    "Days": [90, 365, 365, 365, 365, 365, 365, 365, 365],
    "Avg_Wakt_Prayed": [3.5, 3.5, 3.5, 3.5, 3.0, 3.0, 4.0, 4.0, 4.0]
})

edited_df = st.data_editor(default_data, num_rows="dynamic", key="yearly_input")

# Safeguard against empty dataframes
if edited_df is None or len(edited_df) == 0:
    st.warning("⚠️ Please add at least one year of prayer history above to proceed.")
    st.stop()

# Calculations
edited_df["Total_Wakt"] = edited_df["Days"] * wakts_per_day
edited_df["Actual_Prayed"] = edited_df["Days"] * edited_df["Avg_Wakt_Prayed"]
edited_df["Missed"] = edited_df["Total_Wakt"] - edited_df["Actual_Prayed"]

total_obligatory = edited_df["Total_Wakt"].sum()
total_actual = edited_df["Actual_Prayed"].sum()
total_missed = edited_df["Missed"].sum()
num_years = len(edited_df)

st.divider()

# ==========================================
# STEP 2: SUMMARY & OVERESTIMATION
# ==========================================
st.header("Step 2: Summary & Overestimated Buffer")

col1, col2, col3 = st.columns(3)
col1.metric("Total Obligatory Prayers", f"{total_obligatory:,.0f}")
col2.metric("Total Actual Prayed", f"{total_actual:,.1f}")
col3.metric("Calculated Missed Prayers", f"{total_missed:,.1f}")

# Default recommended overestimated target (rounded up to nearest 1000)
default_overestimated = int(np.ceil(total_missed / 1000.0) * 1000)

st.markdown("### Overestimation & Manual Override")
st.markdown("To ensure complete spiritual peace of mind, the system suggests rounding up your missed prayers to the nearest 1,000. You can manually edit this amount below if desired.")

overestimated_target = st.number_input(
    "Overestimated Target Amount (Wakts)",
    min_value=0,
    value=
