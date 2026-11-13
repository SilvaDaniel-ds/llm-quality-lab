"""LLM Quality Lab — a small public dataset review app."""

import csv
from datetime import datetime, timezone
from html import escape
from io import StringIO
import random
import secrets

import requests
import streamlit as st

from data_source import DATA_SOURCES, load_pairs, source_link
from review_stats import review_summary

st.set_page_config(page_title="LLM Quality Lab | Daniel Silva", page_icon="🔎", layout="wide")


@st.cache_data(ttl=1800, show_spinner=False)
def fetch_rows(source, start, count):
    return load_pairs(source, start, count)


def safe_csv_value(value):
    """Prevent formulas from running when CSV files are opened in spreadsheets."""
    value = str(value if value is not None else "")
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value


def review_csv(reviews):
    columns = [
        "dataset", "split", "row_id", "choice", "source_preferred",
        "matches_source", "main_reason", "notes", "reviewed_at_utc",
    ]
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    for review in reviews:
        writer.writerow({field: safe_csv_value(review.get(field, "")) for field in columns})
    return output.getvalue()


def content_card(text, extra_class=""):
    """Show dataset text as text, not as HTML that can run in the browser."""
    clean = escape(text, quote=True)
    st.markdown(
        f'<div class="content-card {extra_class}"><div class="content-text">{clean}</div></div>',
        unsafe_allow_html=True,
    )


st.markdown("""
<style>
    .block-container {max-width: 1320px; padding-top: 2rem; padding-bottom: 4rem;}
    [data-testid="stAppViewContainer"] {background: #f5f7fb;}
    [data-testid="stSidebar"] {background: #ffffff; border-right: 1px solid #e6eaf2;}
    [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 {color: #13203b;}
    .hero {
        padding: 32px 36px; border-radius: 18px;
        background: linear-gradient(115deg, #102341 5%, #193d64 70%, #175873 100%);
        color: white; margin-bottom: 25px; box-shadow: 0 12px 30px rgba(14,38,70,.10);
    }
    .eyebrow {font-size: 12px; font-weight: 750; letter-spacing: 2.0px; color: #8ed5e9; margin-bottom: 12px;}
    .hero h1 {color:#fff; font-size: 34px; font-weight: 760; letter-spacing: -.8px; margin:0 0 8px;}
    .hero p {color:#dce8f3; font-size: 15px; max-width: 670px; margin:0; line-height:1.6;}
    .section-label {font-size: 12px; color: #64748b; letter-spacing: 1.3px; font-weight:700; text-transform:uppercase;}
    .source-note {color: #60708b; font-size: 13px; margin: 2px 0 18px;}
    .content-card {
        background: #fff; border: 1px solid #dfe6f1; border-radius: 14px;
        padding: 21px 22px; box-shadow: 0 4px 16px rgba(19,39,74,.035);
        min-height: 260px; overflow-y: auto; max-height: 440px;
    }
    .content-card.prompt {max-height: 250px; min-height: 115px; background: #fbfdff;}
    .content-text {white-space: pre-wrap; overflow-wrap: anywhere; font-family: inherit;
        font-size: 14px; line-height: 1.68; color: #1f2c42;}
    .answer-title {font-size: 18px; font-weight: 730; color:#13203b; margin: 9px 0 12px;}
    .letter {display:inline-flex; justify-content:center;align-items:center;
        width:30px;height:30px;border-radius:9px;background:#e3eaf7;color:#1e4b81;margin-right:8px;font-weight:800;}
    .row-meta {font-size: 13px; color: #68788f; margin-bottom: 13px;}
    [data-testid="stMetric"] {background: white; border:1px solid #e1e7f0;
        padding:17px 18px;border-radius:13px;}
    [data-testid="stMetricLabel"] {color: #66768c;}
    [data-testid="stMetricValue"] {color: #152841;}
    [data-testid="stForm"] {background:#fff; border:1px solid #e1e7f0; border-radius:15px; padding:22px;}
    .app-footer {font-size:12px; color:#718096; margin-top:28px; padding-top:15px; border-top:1px solid #e1e7f0;}
    @media (max-width: 700px) {.hero {padding:24px;} .hero h1 {font-size:26px;} .block-container{padding-top:1rem;}}
</style>
""", unsafe_allow_html=True)

if "reviews" not in st.session_state:
    st.session_state.reviews = {}
if "review_seed" not in st.session_state:
    st.session_state.review_seed = secrets.randbits(48)

with st.sidebar:
    st.markdown("### Review settings")
    source = st.selectbox("Dataset", options=list(DATA_SOURCES), index=0)
    settings = DATA_SOURCES[source]
    st.caption(f"Language: {settings['language']}")
    start = st.number_input("Start at row", min_value=0, value=0, step=10)
    count = st.selectbox("Rows to load", options=[5, 10, 20], index=1)
    st.link_button("Open the dataset", source_link(source), use_container_width=True)
    st.divider()
    st.markdown("**About the labels**")
    st.caption(settings["label_note"])
    st.info("Your reviews are saved only in this browser session. Export the CSV to keep them.")

st.markdown("""
<div class="hero">
  <div class="eyebrow">AI QUALITY / HUMAN REVIEW</div>
  <h1>LLM Quality Lab</h1>
  <p>Review real model responses. Make your own choice, then compare it with a public preference label.</p>
</div>
""", unsafe_allow_html=True)

st.markdown("<div class='section-label'>01 / Choose a response pair</div>", unsafe_allow_html=True)
try:
    with st.spinner("Loading responses from Hugging Face..."):
        pairs = fetch_rows(source, int(start), int(count))
except (requests.RequestException, ValueError, KeyError, TypeError) as error:
    st.error("We couldn't load this dataset right now. Try a different starting row or try again later.")
    with st.expander("Technical details"):
        st.code(str(error))
    st.stop()

if not pairs:
    st.warning("No usable response pairs in this batch. Try another starting row.")
    st.stop()

pairs_by_label = {f"Row {pair['row_id']}": pair for pair in pairs}
selected_label = st.selectbox("Record", options=list(pairs_by_label))
pair = pairs_by_label[selected_label]
row_id = pair["row_id"]
record_key = f"{settings['dataset']}:{settings['config']}:{settings['split']}:{row_id}"

# Flip the original labels so the review is blind, but stable during a session.
reversed_order = random.Random(f"{st.session_state.review_seed}:{record_key}").choice([True, False])
response_a = pair["rejected"] if reversed_order else pair["chosen"]
response_b = pair["chosen"] if reversed_order else pair["rejected"]
source_preferred = "B" if reversed_order else "A"

st.markdown(
    f"<div class='row-meta'>Source: {escape(settings['dataset'])} &nbsp; · &nbsp; "
    f"Language: {escape(settings['language'])} &nbsp; · &nbsp; ID: {row_id}</div>",
    unsafe_allow_html=True,
)

st.markdown("<div class='section-label'>02 / Read the original prompt</div>", unsafe_allow_html=True)
content_card(pair["prompt"], "prompt")
st.write("")
st.markdown("<div class='section-label'>03 / Compare the answers</div>", unsafe_allow_html=True)
left, right = st.columns(2, gap="medium")
with left:
    st.markdown('<div class="answer-title"><span class="letter">A</span>Response A</div>', unsafe_allow_html=True)
    content_card(response_a)
with right:
    st.markdown('<div class="answer-title"><span class="letter">B</span>Response B</div>', unsafe_allow_html=True)
    content_card(response_b)

st.write("")
st.markdown("<div class='section-label'>04 / Make your choice</div>", unsafe_allow_html=True)
previous = st.session_state.reviews.get(record_key)
if previous:
    st.success("This pair is saved in your session.")
    st.write(f"**Your choice:** {previous['choice']}  ·  **Dataset preference:** {previous['source_preferred']}")
    st.caption("Move to another record to continue. Your saved decision will stay in the CSV export.")
else:
    with st.form(key=f"review_form_{record_key}"):
        choice = st.radio("Which response is better?", ["A", "B", "Tie", "Not sure"], index=None, horizontal=True)
        reason = st.selectbox(
            "Main reason (optional)",
            ["Not selected", "Instruction following", "Accuracy", "Clarity", "Completeness", "Safety", "Tone / style", "Other"],
        )
        notes = st.text_area("Notes (optional)", placeholder="What made one response better?", height=90)
        submitted = st.form_submit_button("Save review", type="primary", use_container_width=True)
        if submitted:
            if choice is None:
                st.warning("Choose A, B, Tie, or Not sure before saving.")
            else:
                st.session_state.reviews[record_key] = {
                    "dataset": settings["dataset"],
                    "split": settings["split"],
                    "row_id": row_id,
                    "choice": choice,
                    "source_preferred": source_preferred,
                    "matches_source": choice == source_preferred if choice in ("A", "B") else "",
                    "main_reason": "" if reason == "Not selected" else reason,
                    "notes": notes.strip(),
                    "reviewed_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                }
                st.rerun()

st.divider()
st.markdown("### Session results")
reviews = list(st.session_state.reviews.values())
summary = review_summary(reviews)
col1, col2, col3 = st.columns(3)
col1.metric("Saved reviews", summary["saved"])
col2.metric("A/B decisions", summary["decided"])
col3.metric("Agreement with labels", f"{summary['agreement_percent']}%" if summary["decided"] else "—")
st.caption("Agreement only counts A/B decisions. Tie and Not sure are not included. This is not a model accuracy score.")

if reviews:
    with st.expander("Review history", expanded=True):
        st.dataframe(reviews, use_container_width=True, hide_index=True)
    st.download_button(
        "Download reviews · CSV", review_csv(reviews), "llm_quality_reviews.csv",
        mime="text/csv", use_container_width=False,
    )
else:
    st.info("Your saved reviews will show up here after your first decision.")

st.markdown(
    '<div class="app-footer">Independent project by Daniel Silva. Public research data from Hugging Face. '
    'No private company examples, internal rules, or employer data are used.</div>',
    unsafe_allow_html=True,
)
