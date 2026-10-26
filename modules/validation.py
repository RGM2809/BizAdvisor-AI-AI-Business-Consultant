
import pandas as pd


REQUIRED_COLUMNS = [
    "transaction_date",
    "product_name",
    "quantity",
    "unit_price",
]

OPTIONAL_COLUMNS = ["total_amount"]


def validate_sales_data(dataframe):
    """
    Return (accepted_dataframe, issues_dataframe).

    Each issue includes the original row number, field and reason.
    """
    data = dataframe.copy().reset_index(drop=True)
    issues = []

    def add_issue(index, field, reason):
        issues.append({
            "row": index + 2,
            "field": field,
            "issue": reason,
        })

    for column in REQUIRED_COLUMNS:
        if column not in data.columns:
            return (
                pd.DataFrame(columns=[
                    "transaction_date", "product_name",
                    "quantity", "unit_price", "total_amount"
                ]),
                pd.DataFrame([{
                    "row": "All",
                    "field": column,
                    "issue": f"Required column '{column}' is missing."
                }])
            )

    if "total_amount" not in data.columns:
        data["total_amount"] = pd.NA

    # Preserve source transaction IDs when provided.
    has_source_id = "transaction_id" in data.columns
    if has_source_id:
        source_ids = data["transaction_id"].astype("string").str.strip()
        source_ids = source_ids.mask(source_ids == "")
    else:
        source_ids = pd.Series(pd.NA, index=data.index, dtype="string")

    parsed_dates = pd.to_datetime(
        data["transaction_date"],
        errors="coerce"
    )
    date_text = parsed_dates.dt.strftime("%Y-%m-%d")

    product_text = data["product_name"].astype("string").str.strip()

    for index in data.index:
        if pd.isna(parsed_dates.iloc[index]):
            add_issue(index, "transaction_date", "Invalid or missing date.")

        if pd.isna(product_text.iloc[index]) or not product_text.iloc[index]:
            add_issue(index, "product_name", "Product name is missing.")

    quantity = pd.to_numeric(data["quantity"], errors="coerce")
    unit_price = pd.to_numeric(data["unit_price"], errors="coerce")
    total = pd.to_numeric(data["total_amount"], errors="coerce")

    for index in data.index:
        if pd.isna(quantity.iloc[index]) or quantity.iloc[index] <= 0:
            add_issue(index, "quantity", "Quantity must be greater than zero.")

        if pd.isna(unit_price.iloc[index]) or unit_price.iloc[index] < 0:
            add_issue(index, "unit_price", "Unit price must be zero or greater.")

        if not pd.isna(total.iloc[index]) and total.iloc[index] < 0:
            add_issue(index, "total_amount", "Total must not be negative.")

    calculated_total = quantity * unit_price
    final_total = total.copy()

    for index in data.index:
        if pd.isna(final_total.iloc[index]):
            final_total.iloc[index] = calculated_total.iloc[index]
        elif (
            not pd.isna(calculated_total.iloc[index])
            and abs(final_total.iloc[index] - calculated_total.iloc[index]) > 0.01
        ):
            add_issue(
                index,
                "total_amount",
                "Total differs from quantity × unit price."
            )

    candidate = pd.DataFrame({
        "transaction_date": date_text,
        "product_name": product_text,
        "quantity": quantity,
        "unit_price": unit_price,
        "total_amount": final_total,
    })

    candidate["product_name"] = (
        candidate["product_name"].astype("string").str.strip().str.casefold()
    )

    duplicate_columns = [
        "transaction_date", "product_name",
        "quantity", "unit_price", "total_amount"
    ]

    duplicate_mask = candidate.duplicated(
        subset=duplicate_columns,
        keep="first"
    )

    if has_source_id:
        # Different non-empty source IDs establish separate transactions.
        previous_id_by_sale = {}
        for index in candidate.index:
            if not duplicate_mask.iloc[index]:
                key = tuple(candidate.loc[index, duplicate_columns].tolist())
                if pd.notna(source_ids.iloc[index]):
                    previous_id_by_sale.setdefault(key, set()).add(
                        source_ids.iloc[index]
                    )

        for index in candidate.index[duplicate_mask]:
            key = tuple(candidate.loc[index, duplicate_columns].tolist())
            current_id = source_ids.iloc[index]
            known_ids = previous_id_by_sale.get(key, set())

            if pd.notna(current_id) and known_ids and current_id not in known_ids:
                duplicate_mask.iloc[index] = False
            else:
                add_issue(index, "record", "Potential duplicate sales record; review before excluding.")

    else:
        for index in candidate.index[duplicate_mask]:
            add_issue(index, "record", "Potential duplicate sales record; review before excluding.")

    issue_frame = pd.DataFrame(
        issues,
        columns=["row", "field", "issue"]
    )

    invalid_indices = {
        int(item["row"]) - 2
        for item in issues
        if isinstance(item["row"], int)
    }

    valid_indices = [
        index for index in data.index
        if index not in invalid_indices
    ]

    accepted = candidate.loc[valid_indices].copy()
    accepted["product_name"] = (
        accepted["product_name"].astype("string").str.strip()
    )

    if has_source_id:
        accepted.insert(0, "transaction_id", source_ids.loc[valid_indices])

    return accepted.reset_index(drop=True), issue_frame
