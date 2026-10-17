import io
import math
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
# SIDEBAR SETTINGS & TOGGLES
# ==========================================
st.sidebar.header("⚙️ Configuration Settings")
include_witr = st.sidebar.checkbox(
    "Include Witr Prayer (6 Wakts / Day)", 
    value=True, 
    help="In Hanafi jurisprudence, Witr is Wajib and made up alongside Isha."
)
wakts_per_day = 6 if include_witr else 5

# ==========================================
# STEP 1: MANUAL YEARLY INPUTS
# ==========================================
st.header("Step 1: Enter Your Yearly Prayer History")
st.markdown("Add your prayer history year by year. Enter how many valid days you prayed that year and your average wakts prayed per day.")

default_data = pd.DataFrame({
    "Year": [2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025],
    "Days": [90, 365, 365, 365, 365, 365, 365, 365, 365],
    "Avg_Wakt_Prayed": [3.5, 3.5, 3.5, 3.5, 3.0, 3.0, 4.0, 4.0, 4.0]
})

# Lock column creation & prevent extra columns
edited_df = st.data_editor(
    default_data, 
    num_rows="dynamic", 
    key="yearly_input",
    column_config={
        "Year": st.column_config.NumberColumn("Year", min_value=1900, max_value=2100, step=1, format="%d"),
        "Days": st.column_config.NumberColumn("Valid Days Prayed", min_value=0, max_value=366, step=1),
        "Avg_Wakt_Prayed": st.column_config.NumberColumn(f"Avg Wakt Prayed (Max {wakts_per_day})", min_value=0.0, max_value=float(wakts_per_day), step=0.1)
    }
)

# Safeguard against empty dataframes or NaN cells
if edited_df is None or len(edited_df) == 0:
    st.warning("⚠️ Please enter at least one valid year in the table above to proceed.")
    st.stop()

# Clean missing/blank values instantly
cleaned_df = edited_df.fillna(0).copy()

# Calculations with math.ceil rounding to guarantee whole integers
cleaned_df["Total_Wakt"] = cleaned_df["Days"].apply(lambda x: math.ceil(x * wakts_per_day))
cleaned_df["Actual_Prayed"] = (cleaned_df["Days"] * cleaned_df["Avg_Wakt_Prayed"]).apply(math.ceil)
cleaned_df["Missed"] = (cleaned_df["Total_Wakt"] - cleaned_df["Actual_Prayed"]).clip(lower=0).apply(math.ceil)

total_obligatory = int(cleaned_df["Total_Wakt"].sum())
total_actual = int(cleaned_df["Actual_Prayed"].sum())
total_missed = int(cleaned_df["Missed"].sum())
num_years = len(cleaned_df)

st.divider()

# ==========================================
# STEP 2: SUMMARY & OVERESTIMATION
# ==========================================
st.header("Step 2: Summary & Overestimated Buffer")

col1, col2, col3 = st.columns(3)
col1.metric("Total Obligatory Prayers", f"{total_obligatory:,}")
col2.metric("Total Actual Prayed", f"{total_actual:,}")
col3.metric("Calculated Missed Prayers", f"{total_missed:,}")

# Default recommended overestimated target (rounded up to nearest 1000)
default_overestimated = int(math.ceil(total_missed / 1000.0) * 1000) if total_missed > 0 else 1000

st.markdown("### Overestimation & Manual Override")
st.markdown("To ensure complete spiritual peace of mind, the system suggests rounding up your missed prayers to the nearest 1,000. You can manually edit this amount below if desired.")

overestimated_target = st.number_input(
    "Overestimated Target Amount (Wakts)",
    min_value=0,
    value=default_overestimated,
    step=500
)

st.divider()

# ==========================================
# STEP 3: MANUAL LIFETIME ALLOCATION
# ==========================================
st.header("Step 3: Lifetime Prayer Allocation")
st.markdown(f"Manually allocate your target of **{overestimated_target:,} prayers** across your daily prayers based on your estimation. Yearly allocations will be divided automatically across **{num_years} years**.")

if include_witr:
    col_a, col_b, col_c, col_d, col_e, col_f = st.columns(6)
    alloc_fazr = col_a.number_input("Fazr", min_value=0, value=int(overestimated_target * 0.40))
    alloc_zuhr = col_b.number_input("Zuhr", min_value=0, value=int(overestimated_target * 0.12))
    alloc_asr = col_c.number_input("Asr", min_value=0, value=int(overestimated_target * 0.12))
    alloc_magrib = col_d.number_input("Magrib", min_value=0, value=int(overestimated_target * 0.12))
    alloc_esha = col_e.number_input("Esha", min_value=0, value=int(overestimated_target * 0.12))
    alloc_witr = col_f.number_input("Witr", min_value=0, value=int(overestimated_target * 0.12))
    allocations_dict = {'Fazr': alloc_fazr, 'Zuhr': alloc_zuhr, 'Asr': alloc_asr, 'Magrib': alloc_magrib, 'Esha': alloc_esha, 'Witr': alloc_witr}
else:
    col_a, col_b, col_c, col_d, col_e = st.columns(5)
    alloc_fazr = col_a.number_input("Fazr", min_value=0, value=int(overestimated_target * 0.48))
    alloc_zuhr = col_b.number_input("Zuhr", min_value=0, value=int(overestimated_target * 0.13))
    alloc_asr = col_c.number_input("Asr", min_value=0, value=int(overestimated_target * 0.13))
    alloc_magrib = col_d.number_input("Magrib", min_value=0, value=int(overestimated_target * 0.13))
    alloc_esha = col_e.number_input("Esha", min_value=0, value=int(overestimated_target * 0.13))
    allocations_dict = {'Fazr': alloc_fazr, 'Zuhr': alloc_zuhr, 'Asr': alloc_asr, 'Magrib': alloc_magrib, 'Esha': alloc_esha}

total_allocated = sum(allocations_dict.values())
allocation_gap = overestimated_target - total_allocated

# Strict Gap Validation
if allocation_gap != 0:
    st.error(f"⚠️ **Allocation Mismatch:** Your allocated total ({total_allocated:,}) does not equal your Overestimated Target ({overestimated_target:,}). Difference: **{allocation_gap:+,} prayers**. Please adjust your manual allocations before printing.")
    can_print = False
else:
    st.success("✅ Lifetime allocation matches your target perfectly!")
    can_print = True

# Yearly split calculation with math.ceil
yearly_alloc = {prayer: math.ceil(count / num_years) for prayer, count in allocations_dict.items()}

# Display allocation summary table
alloc_summary_df = pd.DataFrame({
    "Prayer": list(allocations_dict.keys()) + ["Total"],
    "Lifetime Target": list(allocations_dict.values()) + [total_allocated],
    "Yearly Allocation": list(yearly_alloc.values()) + [sum(yearly_alloc.values())]
})
st.table(alloc_summary_df)

st.divider()

# ==========================================
# STEP 4: PRINTABLE PDF GENERATOR
# ==========================================
st.header("Step 4: Generate Printable PDF Tracker")
st.markdown(f"Every year starts on a brand-new page with its respective **Year Title Header** and round-square checkboxes. Estimated print length: **{num_years + 1} pages** (1 master page + {num_years} yearly pages).")

def make_rounded_checkbox_grid(count, cols=15):
    cells = []
    row = []
    for i in range(1, count + 1):
        d = Drawing(14, 14)
        # Round square shape: rx=3, ry=3
        d.add(Rect(1, 1, 12, 12, rx=3, ry=3, fillColor=colors.white, strokeColor=colors.HexColor("#4A5568"), strokeWidth=1))
        row.append(d)
        if len(row) == cols:
            cells.append(row)
            row = []
    if row:
        while len(row) < cols:
            row.append(Drawing(14, 14))
        cells.append(row)
    
    t = Table(cells, colWidths=[18]*cols)
    t.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    return t

def generate_pdf_bytes():
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'TitleStyle', parent=styles['Heading1'], fontSize=18, leading=22, alignment=1, textColor=colors.HexColor("#1A365D")
    )
    subtitle_style = ParagraphStyle(
        'SubTitleStyle', parent=styles['Heading2'], fontSize=12, leading=16, alignment=1, textColor=colors.HexColor("#4A5568")
    )

    # Page 1: Master Summary
    story.append(Paragraph("<b>Personal Qaza Prayer Tracker & Master Summary</b>", title_style))
    story.append(Spacer(1, 15))
    
    min_year = int(cleaned_df['Year'].min()) if not cleaned_df.empty else 2017
    max_year = int(cleaned_df['Year'].max()) if not cleaned_df.empty else 2025

    summary_data = [
        ["Metric / Description", "Value"],
        ["Total Obligatory Prayers", f"{total_obligatory:,}"],
        ["Total Actual Prayed", f"{total_actual:,}"],
        ["Total Missed (Calculated)", f"{total_missed:,}"],
        ["Overestimated Amount (Target)", f"{overestimated_target:,}"]
    ]
    t1 = Table(summary_data, colWidths=[250, 150])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1A365D")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F7FAFC")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
    ]))
    story.append(t1)
    story.append(Spacer(1, 20))
    
    story.append(Paragraph(f"<b>Lifetime & Yearly Allocation ({num_years} Years: {min_year} - {max_year})</b>", subtitle_style))
    story.append(Spacer(1, 10))
    
    alloc_table_data = [["Prayer", "Lifetime Target", "Yearly Allocation"]]
    for prayer, total in allocations_dict.items():
        alloc_table_data.append([prayer, f"{total:,}", f"{yearly_alloc[prayer]:,}"])
    
    t2 = Table(alloc_table_data, colWidths=[150, 150, 150])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F7FAFC")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
    ]))
    story.append(t2)
    story.append(PageBreak())

    # Yearly Pages with Year Title Headers
    years = cleaned_df['Year'].astype(int).tolist()
    for idx, year in enumerate(years):
        # Header displaying the year title on every page
        story.append(Paragraph(f"<b>Qaza Prayer Tracker — Year {year}</b>", title_style))
        story.append(Spacer(1, 10))
        
        for prayer, count in yearly_alloc.items():
            story.append(Paragraph(f"<b>{prayer}</b> (Target: {count} prayers)", ParagraphStyle('PH', parent=styles['Heading3'], fontSize=11, textColor=colors.HexColor("#2D3748"))))
            story.append(Spacer(1, 4))
            story.append(make_rounded_checkbox_grid(count, cols=15))
            story.append(Spacer(1, 8))
            
        if idx < len(years) - 1:
            story.append(PageBreak())

    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()

# Single-click download button or blocked state
if can_print:
    st.download_button(
        label="📥 Download Printable PDF Tracker",
        data=generate_pdf_bytes(),
        file_name="Qaza_Prayer_Tracker_Printable.pdf",
        mime="application/pdf",
        type="primary"
    )
else:
    st.button("📥 Download Printable PDF Tracker", disabled=True, help="Fix the allocation gap above to enable PDF generation.")
