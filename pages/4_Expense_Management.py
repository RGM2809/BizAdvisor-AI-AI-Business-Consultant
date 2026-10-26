
import streamlit as st
import pandas as pd

from database.connection import initialize_database
from modules.business_selector import select_business
from modules.expense_management import (
    EXPENSE_CATEGORIES,
    add_expense,
    get_expenses,
    delete_expense,
)


# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Expense Management | BizAdvisor AI",
    page_icon="🧾",
    layout="wide",
)

initialize_database()

st.title("🧾 Expense Management")
st.write(
    "Record and manage business expenses to understand "
    "where your money is going."
)


# --------------------------------------------------
# Use the shared business selection
# --------------------------------------------------

business = select_business()

if business is None:
    st.info(
        "Choose a business from the sidebar before managing expenses."
    )
    st.stop()

business_id = int(business["business_id"])
business_name = business["business_name"]
currency = business.get("currency") or "INR"

st.caption(f"Managing expenses for: **{business_name}**")


# --------------------------------------------------
# Add expense form
# --------------------------------------------------

st.divider()
st.subheader("Add a New Expense")

with st.form("add_expense_form", clear_on_submit=True):

    expense_date = st.date_input("Expense Date")

    category = st.selectbox(
        "Expense Category",
        EXPENSE_CATEGORIES,
    )

    amount = st.number_input(
        "Expense Amount",
        min_value=0.01,
        value=100.0,
        step=10.0,
    )

    description = st.text_input(
        "Description (Optional)",
        placeholder="Example: Monthly electricity bill",
    )

    submitted = st.form_submit_button(
        "Save Expense",
        type="primary",
    )


# --------------------------------------------------
# Save expense
# --------------------------------------------------

if submitted:
    try:
        expense_id = add_expense(
            business_id=business_id,
            expense_date=expense_date,
            category=category,
            amount=amount,
            description=description,
        )

        st.success(
            f"Expense saved successfully! Expense ID: {expense_id}"
        )

    except (ValueError, TypeError) as error:
        st.error(str(error))

    except Exception as error:
        st.error("Could not save the expense.")
        st.exception(error)


# --------------------------------------------------
# Retrieve saved expenses for this business
# --------------------------------------------------

st.divider()
st.subheader("Saved Expenses")

try:
    expenses = get_expenses(business_id)

except Exception as error:
    st.error("Could not retrieve expenses.")
    st.exception(error)
    st.stop()

if expenses.empty:
    st.info("No expenses recorded for this business yet.")

else:
    total_expenses = float(expenses["amount"].sum())

    st.metric(
        "Total Recorded Expenses",
        f"{currency} {total_expenses:,.2f}",
    )

    st.dataframe(
        expenses,
        use_container_width=True,
        hide_index=True,
    )

    # --------------------------------------------------
    # Expense category summary
    # --------------------------------------------------

    st.subheader("Expenses by Category")

    category_summary = (
        expenses.groupby("category", as_index=False)
        .agg(
            total_amount=("amount", "sum"),
            expense_count=("expense_id", "count"),
        )
        .sort_values("total_amount", ascending=False)
    )

    st.dataframe(
        category_summary,
        use_container_width=True,
        hide_index=True,
    )

    # --------------------------------------------------
    # Delete an expense
    # --------------------------------------------------

    st.divider()
    st.subheader("Delete an Expense")

    expense_options = {
        (
            f"ID {row.expense_id} | {row.category} | "
            f"{currency} {row.amount:,.2f} | {row.expense_date}"
        ): int(row.expense_id)
        for row in expenses.itertuples()
    }

    selected_expense_label = st.selectbox(
        "Select expense to delete",
        list(expense_options.keys()),
    )

    confirm_delete = st.checkbox(
        "I confirm that I want to delete this expense."
    )

    if st.button("Delete Selected Expense", type="secondary"):
        if not confirm_delete:
            st.warning("Please confirm before deleting the expense.")
        else:
            try:
                deleted = delete_expense(
                    expense_options[selected_expense_label],
                    business_id,
                )

                if deleted:
                    st.success("Expense deleted successfully.")
                    st.rerun()
                else:
                    st.warning("The expense was not found.")

            except Exception as error:
                st.error("Could not delete the expense.")
                st.exception(error)
