
import streamlit as st

from modules.business_selector import select_business
from modules.business_qa import answer_business_question

st.title("Business Q&A Assistant")
st.write(
    "Ask questions about your recorded sales, expenses, "
    "product performance, and business finances."
)

business = select_business()

if business is None:
    st.info("Select a business from the sidebar to get started.")
    st.stop()

business_id = int(business["business_id"])
st.caption(f"Answering questions about: {business['business_name'] if 'business_name' in business else business.get('name', 'Selected business')}")

st.divider()

st.subheader("Ask your business a question")

examples = [
    "What is my total revenue?",
    "What are my biggest expenses?",
    "Am I operating at a loss?",
    "Which product generates the most revenue?",
    "How can I improve my business?",
]

for example in examples:
    if st.button(example, use_container_width=True):
        st.session_state["business_qa_question"] = example

with st.form("business_qa_form"):
    question = st.text_input(
        "Your question",
        value=st.session_state.get("business_qa_question", ""),
        placeholder="Example: What is my total revenue?",
    )
    submitted = st.form_submit_button(
        "Ask Question",
        type="primary",
    )

if submitted:
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        answer = answer_business_question(business_id, question)
        st.session_state["business_qa_last_question"] = question
        st.session_state["business_qa_last_answer"] = answer

if st.session_state.get("business_qa_last_answer"):
    st.subheader("Answer")
    st.markdown(
        f"**You asked:** {st.session_state['business_qa_last_question']}"
    )
    st.write(st.session_state["business_qa_last_answer"])

st.caption(
    "Answers are based on recorded business data and simple rules. "
    "They are not financial guarantees."
)
