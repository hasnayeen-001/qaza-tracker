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
st.set_page_config(page_title="Personal Habit & Recovery Tracker System", page_icon="🕋", layout="wide")

st.title("🕋 Automated Qaza Prayer Tracker & Printable Generator")
st.markdown("Calculate your missed prayers, adjust your **safety margin**, allocate your lifetime debts across the 5 daily prayers, and generate a **print-ready PDF**.")

# ==========================================
# STEP 1: YEAR RANGE SELECTOR & HISTORY
# ==========================================
st.header("Step 1: Select Your Year Range & Prayer History")
st.markdown("""
Select your starting year (such as the year of puberty) and ending year to generate your table. 

By default, **Adjusted Days** is set to 365, but you can edit it directly in the table to deduct days for a mid-year puberty start or menses. You can also adjust your **Avg Wakt Prayed** for each year.
""")
col_yr1, col_yr2 = st.columns(2)
start_year = col_yr1.number_input("Start Year", min_value=1900, max_value=2300, value=2020, step=1)
end_year = col_yr2.number_input("End Year", min_value=1900, max_value=2300, value=2026, step=1)

if start_year > end_year:
    st.error("⚠️ Start Year cannot be later than End Year. Please adjust your range.")
    st.stop()

# Session State to manage the dynamic year range table smoothly without resetting user edits
range_key = f"df_{start_year}_{end_year}"
if range_key not in st.session_state:
    years = list(range(int(start_year), int(end_year) + 1))
    
    # Define exact default days (150 for the first year, 365 for the rest)
    default_days = [150] + [365] * (len(years) - 1) if len(years) > 1 else [150]
    
    # Define exact default Avg Wakt Prayed values matching your list
    default_avg = [3.0, 3.0, 3.0, 3.5, 3.5, 3.5, 4.0, 4.0, 4.0, 4.0]
    
    # Safely pad or slice if the year length changes
    if len(years) <= len(default_avg):
        table_avg = default_avg[:len(years)]
    else:
        table_avg = default_avg + [4.0] * (len(years) - len(default_avg))

    st.session_state[range_key] = pd.DataFrame({
        "Year": years,
        "Days": default_days,
        "Avg_Wakt_Prayed": table_avg
    })

edited_df = st.data_editor(
    st.session_state[range_key], 
    key=f"editor_{range_key}",
    hide_index=True,
    column_config={
        "Year": st.column_config.NumberColumn("Year", disabled=True, format="%d"),
        "Days": st.column_config.NumberColumn("Adjusted Days", min_value=0, max_value=366, step=1),
        "Avg_Wakt_Prayed": st.column_config.NumberColumn("Avg Wakt Prayed", min_value=0.0, max_value=5.0, step=0.1)
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
alloc_fajr = col_a.number_input("Fajr (F)", min_value=0, value=int(overestimated_target * 0.48))
alloc_zuhr = col_b.number_input("Zuhr (Z)", min_value=0, value=int(overestimated_target * 0.13))
alloc_asr = col_c.number_input("Asr (A)", min_value=0, value=int(overestimated_target * 0.13))
alloc_maghrib = col_d.number_input("Maghrib (M)", min_value=0, value=int(overestimated_target * 0.13))
alloc_isha = col_e.number_input("Isha (I)", min_value=0, value=int(overestimated_target * 0.13))

allocations_dict = {
    'Fajr': alloc_fajr, 
    'Zuhr': alloc_zuhr, 
    'Asr': alloc_asr, 
    'Maghrib': alloc_maghrib, 
    'Isha': alloc_isha
}

initial_map = {
    'Fajr': 'F',
    'Zuhr': 'Z',
    'Asr': 'A',
    'Maghrib': 'M',
    'Isha': 'I'
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
    "Wakt": [f"{p} ({initial_map[p]})" for p in allocations_dict.keys()] + ["Total"],
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

def make_repeating_prayer_table(init_letter, count, cols=15):
    """Creates a single Table containing the Wakt header in Row 0 and checkboxes in sub-rows, with repeatRows=1."""
    styles = getSampleStyleSheet()
    header_style = ParagraphStyle('WaktHeader', parent=styles['Heading3'], fontSize=11, leading=14, textColor=colors.HexColor("#2D3748"))
    
    if count <= 0:
        header_p = Paragraph(f"<b>{init_letter} (Target: 0)</b>", header_style)
        t = Table([[header_p]], colWidths=[535])
        t.setStyle(TableStyle([('BOTTOMPADDING', (0,0), (-1,-1), 6)]))
        return t

    header_p = Paragraph(f"<b>{init_letter} (Target: {count})</b>", header_style)
    
    # Row 0: Header Paragraph spanning across all columns
    table_data = [[header_p] + [''] * (cols - 1)]
    
    # Checkbox drawings
    row = []
    for i in range(1, count + 1):
        d = Drawing(14, 14)
        d.add(Rect(1, 1, 12, 12, rx=3, ry=3, fillColor=colors.white, strokeColor=colors.HexColor("#4A5568"), strokeWidth=1))
        row.append(d)
        if len(row) == cols:
            table_data.append(row)
            row = []
    if row:
        while len(row) < cols:
            row.append(Drawing(14, 14))
        table_data.append(row)

    # colWidths of 18pt each for 15 columns = ~270pt total grid width
    col_widths = [18] * cols

    t = Table(table_data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        # Row 0 (Header) styling: span across 15 columns
        ('SPAN', (0, 0), (cols - 1, 0)),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 4),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        # Checkbox cells styling
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 2),
        ('TOPPADDING', (0, 1), (-1, -1), 2),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))
    return t

@st.cache_data
def generate_pdf_bytes(df, overestimated_target, allocations_dict, yearly_alloc, num_years):
    pdf_buffer = io.BytesIO()

    initial_map_local = {
        'Fajr': 'F',
        'Zuhr': 'Z',
        'Asr': 'A',
        'Maghrib': 'M',
        'Isha': 'I'
    }

    frame = Frame(30, 40, 535, 756, id='normal')
    
    # Page 1 (Summary/Note) - NO running top header line
    summary_template = PageTemplate(id='summary', frames=frame, onPage=lambda c, d: None)
    doc = BaseDocTemplate(pdf_buffer, pagesize=A4, pageTemplates=[summary_template])

    years = df['Year'].astype(int).tolist()
    for y in years:
        def make_year_header(year_val):
            def draw_header(canvas_obj, doc_obj):
                canvas_obj.saveState()
                canvas_obj.setFont("Helvetica-Bold", 14)
                canvas_obj.setFillColor(colors.HexColor("#1A365D"))
                canvas_obj.drawString(30, 815, f"{year_val}")
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
        'TitleStyle', parent=styles['Heading1'], fontSize=16, leading=20, alignment=1, textColor=colors.HexColor("#1A365D")
    )
    h2_style = ParagraphStyle(
        'H2Style', parent=styles['Heading2'], fontSize=12, leading=16, textColor=colors.HexColor("#1A365D"), spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyStyle', parent=styles['Normal'], fontSize=10, leading=14, textColor=colors.HexColor("#2D3748")
    )
    quote_style = ParagraphStyle(
        'QuoteStyle', parent=styles['Normal'], fontSize=11, leading=15, textColor=colors.HexColor("#2B6CB0"), fontName="Helvetica-BoldOblique"
    )

    # Page 1: Custom Personal Accountability & Spiritual Recovery Note
    story.append(Paragraph("<b>Personal Accountability & Spiritual Recovery Note</b>", title_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("“A debt owed to Allah has more right to be paid back.”", quote_style))
    story.append(Paragraph("<font size=9 color='#718096'>— Sahih al-Bukhari (1953)</font>", body_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph("1. Purpose & The Safe Path", h2_style))
    story.append(Paragraph("Among Islamic scholars, there are two primary views regarding prayers missed over a prolonged period:", body_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("• <b>The First View:</b> Intentionally abandoning prayer for long periods is a grave matter that invalidates past obligations upon sincere repentance, meaning making up past years (Qaza) is not required, and one should focus entirely on abundant voluntary (Nafl) prayers.", body_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("• <b>The Majority View (Jumhoor):</b> Missed obligatory prayers remain a binding spiritual debt owed to Allah (SWT) that must be systematically fulfilled and repaid alongside sincere repentance (Tawbah).", body_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("To take the safest path and achieve total peace of mind, this document serves as a structured, personal tool to systematically fulfill all past debts under the majority opinion, ensuring that your obligations to Allah are fully cleared.", body_style))
    story.append(Spacer(1, 12))

    story.append(Paragraph("2. Principle of Privacy & Concealing Shortcomings (Sitr)", h2_style))
    story.append(Paragraph("If a shortfall or sin is <b>strictly personal between you and Allah</b> and <b>does not harm or affect anyone else</b>, Islam strongly encourages keeping it concealed while performing sincere repentance (<i>Tawbah</i>) and good deeds. Islam teaches that if Allah conceals a person's past sins or shortcomings, that person should not expose themselves or publicize those mistakes. Instead, they should turn to Allah in sincere repentance and focus on doing good deeds.", body_style))
    story.append(Spacer(1, 6))
    story.append(Paragraph("To preserve complete confidentiality:", body_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("• <b>Abbreviated Labels:</b> On the following tracker pages, daily prayers are listed strictly by their initial letters (F for Fajr, Z for Zuhr, A for Asr, M for Maghrib, I for Isha). To an outside observer, this document appears only as an ambiguous habit or target checklist.", body_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("• <b>Confidentiality:</b> This document is intended solely for your eyes. Do not share or show this tracker to anyone. Keep your progress private between you and your Creator.", body_style))

    # Yearly Tracker Pages
    for year in years:
        story.append(NextPageTemplate(f'year_{year}'))
        story.append(PageBreak())
        
        for prayer, count in yearly_alloc.items():
            init_letter = initial_map_local[prayer]
            prayer_table = make_repeating_prayer_table(init_letter, count, cols=15)
            story.append(prayer_table)
            story.append(Spacer(1, 8))

    doc.build(story, canvasmaker=NumberedCanvas)
    pdf_buffer.seek(0)
    return pdf_buffer.getvalue()

if can_print:
    st.download_button(
        label="📥 Download Printable PDF Tracker",
        data=generate_pdf_bytes(
            cleaned_df, 
            overestimated_target, 
            allocations_dict, 
            yearly_alloc, 
            num_years
        ),
        file_name="Qaza_Prayer_Tracker_Printable.pdf",
        mime="application/pdf",
        type="primary"
    )
