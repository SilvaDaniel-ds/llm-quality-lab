"""A small tool to review public LLM preference pairs."""

import csv
from datetime import datetime, timezone
from io import StringIO
import random
import secrets

import requests
import streamlit as st

from data_source import DATASET, SOURCE_URL, SUBSET, load_pairs
from review_stats import review_summary

st.set_page_config(page_title="LLM Quality Lab", page_icon="🧪", layout="wide")


@st.cache_data(ttl=3600)
def get_batch(start, size):
    return load_pairs(start, size)


def safe_cell(value):
    """Avoid spreadsheet formulas when opening exported text in Excel."""
    text = str(value or "")
    if text.startswith(("=", "+", "-", "@", "\t", "\r")):
        return "'" + text
    return text


def make_csv(reviews):
    output = StringIO()
    columns = [
        "dataset", "subset", "row_id", "choice", "source_preferred",
        "matches_source", "notes", "reviewed_at_utc",
    ]
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    for item in reviews:
        writer.writerow({key: safe_cell(item.get(key)) for key in columns})
    return output.getvalue()


if "reviews" not in st.session_state:
    st.session_state.reviews = {}
if "review_seed" not in st.session_state:
    st.session_state.review_seed = secrets.randbits(32)

st.title("LLM Quality Lab")
st.write("Review real LLM responses and compare your choices with a public preference dataset.")
st.caption("The original preferences come from a research dataset. They are not human ground truth.")

with st.sidebar:
    st.header("Data")
    st.write("Source: GigaVerbo-v2 Preferences")
    st.caption(f"Subset: {SUBSET}")
    start = st.number_input("Start at row", min_value=0, max_value=10520, value=0, step=10)
    batch_size = st.selectbox("Load rows", [5, 10, 20], index=1)
    st.link_button("View source dataset", SOURCE_URL)
    st.info("Reviews stay in this session. Download your CSV if you want to keep them.")

try:
    with st.spinner("Loading the public dataset..."):
        pairs = get_batch(int(start), int(batch_size))
except (requests.RequestException, ValueError, KeyError) as error:
    st.error("Could not load the dataset. Check the connection or try again later.")
    st.caption(f"Technical detail: {error}")
    st.stop()

if not pairs:
    st.warning("No complete response pairs were found in this batch. Try another starting row.")
    st.stop()

pair_options = {f"Row {pair['row_id']}": pair for pair in pairs}
selected = st.selectbox("Choose a record", list(pair_options))
pair = pair_options[selected]
row_id = pair["row_id"]

# Keep A/B assignments stable during this browser session.
switch_sides = random.Random(f"{st.session_state.review_seed}:{row_id}").choice([True, False])
response_a = pair["rejected"] if switch_sides else pair["chosen"]
response_b = pair["chosen"] if switch_sides else pair["rejected"]
source_preferred = "B" if switch_sides else "A"

st.subheader("Original prompt")
st.text_area("Prompt", value=pair["prompt"], height=160, disabled=True)

left, right = st.columns(2)
with left:
    st.subheader("Response A")
    st.text_area("Response A text", value=response_a, height=340, disabled=True)
with right:
    st.subheader("Response B")
    st.text_area("Response B text", value=response_b, height=340, disabled=True)

st.subheader("Your review")
previous = st.session_state.reviews.get(row_id)
if previous:
    st.success("You already reviewed this row in this session.")
    st.write(f"Your choice: **{previous['choice']}**")
    st.write(f"Dataset preference: **{previous['source_preferred']}**")
    st.caption("Select a new row to continue. Your saved result will stay in the export.")
else:
    choice = st.radio(
        "Which response is better?",
        ["A", "B", "Tie", "Not sure"],
        index=None,
        horizontal=True,
        key=f"choice_{row_id}",
    )
    notes = st.text_area(
        "Reason (optional)",
        placeholder="What worked better? What was missing?",
        key=f"notes_{row_id}",
    )
    if st.button("Save review", type="primary"):
        if choice is None:
            st.warning("Choose an option before saving.")
        else:
            st.session_state.reviews[row_id] = {
                "dataset": DATASET,
                "subset": SUBSET,
                "row_id": row_id,
                "choice": choice,
                "source_preferred": source_preferred,
                "matches_source": choice == source_preferred if choice in ("A", "B") else "",
                "notes": notes.strip(),
                "reviewed_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
            st.rerun()

st.divider()
st.subheader("Session results")
all_reviews = list(st.session_state.reviews.values())
if not all_reviews:
    st.info("No reviews yet. Your results will appear after you save your first review.")
else:
    summary = review_summary(all_reviews)
    col1, col2, col3 = st.columns(3)
    col1.metric("Reviews saved", summary["saved"])
    col2.metric("A/B decisions", summary["decided"])
    col3.metric(
        "Agreement with dataset",
        f"{summary['agreement_percent']}%" if summary["agreement_percent"] is not None else "Not available",
    )
    st.caption("Agreement only counts A/B decisions. Tie and Not sure are excluded.")
    st.dataframe(all_reviews, use_container_width=True, hide_index=True)
    st.download_button(
        "Download reviews (CSV)",
        data=make_csv(all_reviews),
        file_name="llm_quality_reviews.csv",
        mime="text/csv",
    )

st.caption("Data: Polygl0t/GigaVerbo-v2 Preferences (Apache 2.0). Independent project, not connected to any employer.")
