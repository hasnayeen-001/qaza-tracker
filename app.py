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
# ==========================================
st.header("Step 3: Lifetime 5-Wakt Allocation")
st.markdown(f"Manually allocate your target of **{overestimated_target:,} prayers** across the 5 daily prayers based on your estimation. Yearly allocations will be divided automatically across **{num_years} years**.")

col_a, col_b, col_c, col_d, col_e = st.columns(5)
alloc_fajr = col_a.number_input("Fajr", min_value=0, value=int(overestimated_target * 0.48))
alloc_zuhr = col_b.number_input("Zuhr", min_value=0, value=int(overestimated_target * 0.13))
alloc_asr = col_c.number_input("Asr", min_value=0, value=int(overestimated_target * 0.13))
alloc_maghrib = col_d.number_input("Maghrib", min_value=0, value=int(overestimated_target * 0.13))
alloc_isha = col_e.number_input("Isha", min_value=0, value=int(overestimated_target * 0.13))

allocations_dict = {
    'Fajr': alloc_fajr, 
    'Zuhr': alloc_zuhr, 
    'Asr': alloc_asr, 
    'Maghrib': alloc_maghrib, 
    'Isha': alloc_isha
}

total_allocated = sum(allocations_dict.values())
allocation_gap = overestimated_target - total_allocated

if allocation_gap != 0:
    st.error(f"⚠️ **Allocation Mismatch:** Your allocated total ({total_allocated:,}) does not equal your Safety Target ({overestimated_target:,}). Difference: **{allocation_gap:+,} prayers**. Please adjust your manual allocations before printing.")
    can_print = False
else:
    st.success("✅ Lifetime allocation matches your target perfectly!")
    can_print = True

yearly_alloc = {prayer: math.ceil(count / num_years) for prayer, count in allocations_dict.items()}

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
st.markdown("Every year starts on a brand-new page with its respective **Year Title Header** and round-square checkboxes.")

class NumberedCanvas(canvas.Canvas):
    """Canvas to calculate total page count and draw clean footers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_footer(num_pages)
            super().showPage()
        super().save()

    def draw_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 9)
        self.setFillColor(colors.HexColor("#718096"))
        self.drawRightString(565, 20, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()

def make_rounded_checkbox_grid(count, cols=15):
    styles = getSampleStyleSheet()
    if count <= 0:
        return Paragraph("<i>No prayers required</i>", ParagraphStyle('NoneReq', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor("#718096")))
    
    cells = []
    row = []
    for i in range(1, count + 1):
        d = Drawing(14, 14)
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
    
    frame = Frame(30, 40, 535, 756, id='normal')
    
    # Page 1 (Summary) - NO running top header line
    summary_template = PageTemplate(id='summary', frames=frame, onPage=lambda c, d: None)
    doc = BaseDocTemplate(pdf_buffer, pagesize=A4, pageTemplates=[summary_template])

    years = cleaned_df['Year'].astype(int).tolist()
    for y in years:
        def make_year_header(year_val):
            def draw_header(canvas_obj, doc_obj):
                canvas_obj.saveState()
                canvas_obj.setFont("Helvetica-Bold", 12)
                canvas_obj.setFillColor(colors.HexColor("#1A365D"))
                canvas_obj.drawString(30, 815, f"Qaza Prayer Tracker — Year {year_val}")
                canvas_obj.setStrokeColor(colors.HexColor("#CBD5E0"))
                canvas_obj.setLineWidth(0.5)
                canvas_obj.line(30, 805, 565, 805)
                canvas_obj.restoreState()
            return draw_header

        yt = PageTemplate(id=f'year_{y}', frames=frame, onPage=make_year_header(y))
        doc.addPageTemplates([yt])

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
    
    min_year = int(cleaned_df['Year'].min()) if not cleaned_df.empty else start_year
    max_year = int(cleaned_df['Year'].max()) if not cleaned_df.empty else end_year

    summary_data = [
        ["Metric / Description", "Value"],
        ["Total Obligatory Prayers", f"{total_obligatory:,}"],
        ["Total Actual Prayed", f"{total_actual:,}"],
        ["Total Missed (Calculated)", f"{total_missed:,}"],
        ["Safety Margin Target", f"{overestimated_target:,}"]
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

    # Yearly Tracker Pages
    for year in years:
        story.append(NextPageTemplate(f'year_{year}'))
        story.append(PageBreak())
        story.append(Spacer(1, 15))
        
        for prayer, count in yearly_alloc.items():
            story.append(Paragraph(f"<b>{prayer}</b> (Target: {count} prayers)", ParagraphStyle('PH', parent=styles['Heading3'], fontSize=11, textColor=colors.HexColor("#2D3748"))))
            story.append(Spacer(1, 4))
            story.append(make_rounded_checkbox_grid(count, cols=15))
            story.append(Spacer(1, 8))

    doc.build(story, canvasmaker=NumberedCanvas)
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()

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
