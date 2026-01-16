import pandas as pd
import streamlit as st
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import tempfile

st.set_page_config(page_title="Job Status Completion", layout="centered")

st.title("Job Status Completion Analyzer")
st.write("Upload a CSV file to see the percentage of jobs in each status, overall completion, and export results as a PDF.")

uploaded_file = st.file_uploader("Upload CSV", type=["csv"])

EXPECTED_STATUSES = [
    "open",
    "pending",
    "Lead Reviewed",
    "Manager Reviewed",
    "QA Reviewed",
]

# Define what counts as "complete"
COMPLETED_STATUSES = [
    "Lead Reviewed",
    "Manager Reviewed",
    "QA Reviewed",
]

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)

        # Determine which column to use for status
        if "status" in df.columns:
            status_column = "status"
        elif "M" in df.columns:
            status_column = "M"
        else:
            st.error("CSV must contain a 'status' column or column 'M'.")
            st.stop()

        total_jobs = len(df)
        status_counts = df[status_column].value_counts()

        results = []
        for status in EXPECTED_STATUSES:
            count = status_counts.get(status, 0)
            percent = (count / total_jobs) * 100 if total_jobs > 0 else 0
            results.append({
                "Status": status,
                "Jobs": count,
                "Percentage": round(percent, 2)
            })

        result_df = pd.DataFrame(results)

        completed_jobs = sum(status_counts.get(s, 0) for s in COMPLETED_STATUSES)
        overall_completion = (completed_jobs / total_jobs) * 100 if total_jobs > 0 else 0

        st.subheader("Completion Breakdown")
        st.dataframe(result_df, use_container_width=True)

        st.subheader("Overall Completion")
        st.metric(
            label="Jobs Completed",
            value=f"{round(overall_completion, 2)}%",
            delta=f"{completed_jobs} of {total_jobs} jobs"
        )

        def generate_pdf():
            styles = getSampleStyleSheet()
            elements = []

            elements.append(Paragraph("Job Status Completion Report", styles['Title']))
            elements.append(Paragraph(f"Total Jobs: {total_jobs}", styles['Normal']))
            elements.append(Paragraph(f"Overall Completion: {round(overall_completion, 2)}%", styles['Normal']))

            table_data = [["Status", "Jobs", "Percentage (%)"]]
            for _, row in result_df.iterrows():
                table_data.append([
                    row["Status"],
                    str(row["Jobs"]),
                    str(row["Percentage"])
                ])

            table = Table(table_data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ]))

            elements.append(table)

            tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            pdf = SimpleDocTemplate(tmp_file.name)
            pdf.build(elements)

            return tmp_file.name

        if st.button("Export Results as PDF"):
            pdf_path = generate_pdf()
            with open(pdf_path, "rb") as f:
                st.download_button(
                    label="Download PDF",
                    data=f,
                    file_name="job_status_completion_report.pdf",
                    mime="application/pdf"
                )

    except Exception as e:
        st.error(f"Error reading file: {e}")
else:
    st.info("Please upload a CSV file to begin.")
