
import pandas as pd
import streamlit as st

from database.connection import initialize_database
from modules.business_selector import select_business
from modules.data_ingestion import load_sales_file
from modules.validation import validate_sales_data
from modules.storage import (
    save_sales_data,
    get_file_sha256,
    has_imported_sales_file,
)


st.set_page_config(
    page_title="Data Import",
    page_icon="📥",
    layout="wide",
)

initialize_database()

st.title("Sales Data Import")
st.write("Upload sales data or enter sales records manually.")

business = select_business()

if business is None:
    st.info("Choose a business from the sidebar before importing sales data.")
    st.stop()

business_id = int(business["business_id"])
business_name = business["business_name"]

st.caption(f"Importing sales for: **{business_name}**")

if "prepared_sales_data" not in st.session_state:
    st.session_state["prepared_sales_data"] = None

input_method = st.radio(
    "Choose input method",
    ["Upload CSV/Excel", "Manual Entry"],
    horizontal=True,
)

data = None
current_file_hash = None
current_filename = None
duplicate_file = False

if input_method == "Upload CSV/Excel":
    uploaded_file = st.file_uploader(
        "Upload a CSV or XLSX file",
        type=["csv", "xlsx"],
    )

    if uploaded_file is not None:
        try:
            file_bytes = uploaded_file.getvalue()
            current_file_hash = get_file_sha256(file_bytes)
            current_filename = uploaded_file.name

            data = load_sales_file(uploaded_file)

            duplicate_file = has_imported_sales_file(
                business_id,
                current_file_hash,
            )

            st.subheader("Imported Data Preview")
            st.dataframe(data.head(20), use_container_width=True)

            if duplicate_file:
                st.warning(
                    "This exact file has already been imported for "
                    f"{business_name}. No records will be saved again."
                )

        except (ValueError, TypeError) as error:
            st.error(f"Could not read the uploaded file: {error}")
            data = None

else:
    st.caption(
        "Enter one row per product sale. "
        "Dates should be understandable by Pandas, "
        "for example 2026-10-25."
    )

    with st.form("manual_sales_form"):
        sale_date = st.date_input("Sale date")
        product = st.text_input("Product name")

        quantity = st.number_input(
            "Quantity",
            min_value=0.0,
            value=1.0,
            step=1.0,
        )

        unit_price = st.number_input(
            "Unit price",
            min_value=0.0,
            value=0.0,
            step=10.0,
        )

        add_record = st.form_submit_button("Prepare Sales Record")

    if add_record:
        if not product.strip():
            st.error("Enter a product name before preparing the record.")
        else:
            st.session_state["prepared_sales_data"] = pd.DataFrame([{
                "transaction_date": str(sale_date),
                "product_name": product.strip(),
                "quantity": quantity,
                "unit_price": unit_price,
                "total_amount": quantity * unit_price,
            }])
            st.session_state["prepared_sales_business_id"] = business_id

    prepared_data = st.session_state.get("prepared_sales_data")
    prepared_business_id = st.session_state.get(
        "prepared_sales_business_id"
    )

    if prepared_data is not None:
        if prepared_business_id != business_id:
            st.warning(
                "A prepared sale belongs to another business. "
                "Select its original business to save it, "
                "or prepare a new record for this business."
            )
        else:
            data = prepared_data

if data is not None:
    accepted, issues = validate_sales_data(data)

    st.subheader("Validation Results")

    col1, col2 = st.columns(2)
    col1.metric("Accepted records", len(accepted))
    col2.metric("Reported issues", len(issues))

    if not issues.empty:
        st.warning(
            "Some records need correction. "
            "Only records without reported issues can be saved."
        )
        st.dataframe(issues, use_container_width=True)

    if not accepted.empty:
        st.subheader("Records Ready to Save")
        st.dataframe(accepted, use_container_width=True)

        if duplicate_file:
            st.info("Choose a different file if you need to import new data.")
        elif st.button("Save Validated Records", type="primary"):
            try:
                if input_method == "Upload CSV/Excel":
                    saved_count = save_sales_data(
                        business_id,
                        accepted,
                        file_hash=current_file_hash,
                        original_filename=current_filename,
                    )
                else:
                    saved_count = save_sales_data(
                        business_id,
                        accepted,
                    )

                    st.session_state["prepared_sales_data"] = None
                    st.session_state.pop(
                        "prepared_sales_business_id",
                        None,
                    )

                st.success(f"Saved {saved_count} sales records.")

            except (ValueError, TypeError) as error:
                st.error(f"Could not save records: {error}")

    if accepted.empty and issues.empty:
        st.info("No records are available to save.")
