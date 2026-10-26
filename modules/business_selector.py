
import streamlit as st

from modules.business_profile import get_businesses


def select_business():
    """Display the shared business selector and refresh control."""

    businesses = get_businesses() or []

    business_map = {
        int(item["business_id"]): item
        for item in businesses
    }

    if "selected_business_id" not in st.session_state:
        st.session_state["selected_business_id"] = None

    selected_id = st.session_state.get("selected_business_id")

    try:
        selected_id = int(selected_id) if selected_id is not None else None
    except (TypeError, ValueError):
        selected_id = None

    if selected_id not in business_map:
        selected_id = None

    st.session_state["selected_business_id"] = selected_id

    # Initialise the widget from the shared selection.
    if "global_business_selector" not in st.session_state:
        st.session_state["global_business_selector"] = selected_id
    else:
        widget_id = st.session_state["global_business_selector"]

        try:
            widget_id = int(widget_id) if widget_id is not None else None
        except (TypeError, ValueError):
            widget_id = None

        if widget_id not in business_map:
            widget_id = None

        if widget_id != selected_id:
            st.session_state["global_business_selector"] = selected_id

    def update_selection():
        st.session_state["selected_business_id"] = (
            st.session_state["global_business_selector"]
        )

    def refresh_business_list():
        # Reload on the next rerun and preserve the current selection.
        st.session_state["business_selector_refresh_notice"] = True

    # Business dropdown.
    st.sidebar.selectbox(
        "🏪 Select business",
        options=[None] + list(business_map.keys()),
        format_func=lambda business_id: (
            "Choose a business..."
            if business_id is None
            else (
                f"{business_map[business_id]['business_name']} "
                f"(ID: {business_id})"
            )
        ),
        key="global_business_selector",
        on_change=update_selection,
    )

    # Fixed button directly below the dropdown.
    st.sidebar.button(
        "🔄 Refresh Business List",
        key="refresh_business_list",
        on_click=refresh_business_list,
        use_container_width=True,
    )

    if st.session_state.pop("business_selector_refresh_notice", False):
        st.sidebar.success("Business list refreshed.")

    selected_id = st.session_state.get("selected_business_id")

    if not businesses:
        st.sidebar.info("No businesses registered yet.")
        return None

    if selected_id is None:
        st.info("Choose a business from the sidebar to display its data.")
        return None

    return business_map.get(int(selected_id))
