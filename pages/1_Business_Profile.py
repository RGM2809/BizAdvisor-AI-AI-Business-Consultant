
import pandas as pd
import streamlit as st

from database.connection import initialize_database
from modules.business_profile import create_business, get_businesses
from modules.business_selector import select_business


st.set_page_config(
    page_title="Business Profile | BizAdvisor AI",
    page_icon="🏪",
    layout="wide",
)

initialize_database()

st.title("🏪 Business Profile")
st.caption(
    "Register and manage the businesses whose data you want to analyse."
)

# --------------------------------------------------
# 1. SHARED BUSINESS SELECTOR
# --------------------------------------------------

select_business()

st.divider()

# --------------------------------------------------
# 2. REGISTER A BUSINESS
# --------------------------------------------------

st.subheader("Register a Business")

with st.form("business_profile_form", clear_on_submit=True):
    name = st.text_input(
        "Business name",
        placeholder="Example: Sunrise Cafe",
    )

    business_type = st.selectbox(
        "Business type",
        [
            "Choose business type...",
            "Retail",
            "Restaurant / Cafe",
            "E-commerce",
            "Services",
            "Manufacturing",
            "Healthcare",
            "Education",
            "Other",
        ],
        index=0,
    )

    location = st.text_input(
        "Business location (optional)",
        placeholder="City or area",
    )

    currency = st.selectbox(
        "Currency",
        ["INR", "USD", "GBP", "EUR"],
    )

    submitted = st.form_submit_button(
        "Save Business Profile",
        type="primary",
        use_container_width=True,
    )

if submitted:
    if business_type == "Choose business type...":
        st.error("Please choose a business type.")

    else:
        try:
            business_id = create_business(
                name,
                business_type,
                location,
                currency,
            )

            st.success(
                f"Business profile saved successfully. "
                f"Business ID: {business_id}"
            )

            st.info(
                "Select the new business from the sidebar selector "
                "to view its data on the other pages."
            )

        except ValueError as error:
            st.error(str(error))

        except Exception as error:
            st.error(f"Unable to save the business profile: {error}")

# --------------------------------------------------
# 3. DISPLAY ALL REGISTERED BUSINESSES
# --------------------------------------------------

st.divider()
st.subheader("Registered Businesses")

try:
    businesses = get_businesses()

    if businesses:
        businesses_df = pd.DataFrame(businesses)

        st.dataframe(
            businesses_df,
            use_container_width=True,
            hide_index=True,
        )

        st.caption(f"Total registered businesses: {len(businesses)}")

    else:
        st.info(
            "No business profiles have been created yet. "
            "Register your first business using the form above."
        )

except Exception as error:
    st.error(f"Unable to load registered businesses: {error}")
