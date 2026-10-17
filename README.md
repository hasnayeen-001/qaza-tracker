[readme.md](https://github.com/user-attachments/files/33598019/readme.md)
# Direct link without running the code: **https://kaza-tracker.streamlit.app**
\
🕋 Automated Qaza Prayer Tracker & Printable Generator

A clean, privacy-focused Streamlit web application designed for non-coders and individuals looking to calculate, adjust, and track their missed (*Qaza*) obligatory prayers over a lifetime or customized multi-year range.

The system calculates missed prayers, applies a customizable **Safety Margin**, divides obligations across the 5 daily Islamic prayers using standard international nomenclature (**Fajr, Zuhr, Asr, Maghrib, Isha**), and generates a print-ready, high-quality **ReportLab PDF** equipped with custom rounded-corner checkbox grids.

## 🌟 Key Features

* **Dynamic Year Range Selector:** Input your starting year (e.g., year of puberty) and ending year (e.g., current year) to generate an interactive history grid.

* **Non-Judgmental Terminology:** Uses refined, intuitive labels such as **Adjusted Days** (accounting for exemptions or puberty start dates) and **Safety Margin**.

* **Flexible Lifetime Allocation:** Allows manual distribution of missed prayers across the 5 daily prayers to reflect individual habits (e.g., assigning higher counts to Fajr).

## 🚀 Getting Started

### **Prerequisites**

* Python 3.9 or higher installed on your system.

### **Installation**

1. **Clone the repository:**

   ```
   git clone https://github.com/hasnayeen-001/qaza-tracker.git
   cd qaza-tracker
   
   ```

2. **Install required packages:**

   ```
   pip install streamlit reportlab pandas numpy
   
   ```

3. **Run the Streamlit application:**

   ```
   streamlit run app.py
   
   ```

## 📖 How to Use

1. **Step 1: Select Year Range & History**

   * Choose your starting and ending years.

   * Edit the **Adjusted Days** column (default 365) and **Avg Wakt Prayed** column (0.0 to 5.0) for each year.

2. **Step 2: Review Summary & Set Safety Margin**

   * Inspect calculated missed prayers.

   * Adjust your **Final Safety Target** to round up your target for peace of mind.

3. **Step 3: Allocate Lifetime Target**

   * Distribute your total Safety Target across **Fajr, Zuhr, Asr, Maghrib, and Isha**.

   * Ensure the gap reaches zero so the success banner appears.

4. **Step 4: Generate Printable PDF**

   * Click **Download Printable PDF Tracker** to download your multi-page PDF logbook ready for printing.

## 🔒 Privacy & Data Policy

This app runs entirely locally or in your private session. No personal prayer data or log histories are stored on external servers or database storage systems.

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).
