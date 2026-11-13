"""Read a small batch from the public Hugging Face dataset."""

import requests

DATASET = "Polygl0t/gigaverbo-v2-preferences"
SUBSET = "harmless-no-reasoning"
SOURCE_URL = f"https://huggingface.co/datasets/{DATASET}"
ROWS_API = "https://datasets-server.huggingface.co/rows"


def get_text(messages):
    """Turn a list of chat messages into text we can display."""
    if not isinstance(messages, list):
        return ""

    parts = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        content = message.get("content", "")
        if isinstance(content, str) and content.strip():
            parts.append(content.strip())

    return "\n\n".join(parts)


def parse_rows(payload):
    """Keep the row number and original response labels."""
    pairs = []
    for item in payload.get("rows", []):
        row = item.get("row", {})
        prompt = get_text(row.get("prompt"))
        chosen = get_text(row.get("chosen"))
        rejected = get_text(row.get("rejected"))

        if not prompt or not chosen or not rejected:
            continue

        pairs.append({
            "row_id": item.get("row_idx"),
            "prompt": prompt,
            "chosen": chosen,
            "rejected": rejected,
        })

    return pairs


def load_pairs(offset=0, count=10):
    """Get real pairs. No local examples or made-up scores."""
    if offset < 0 or not 1 <= count <= 100:
        raise ValueError("Offset or row count is out of range")

    response = requests.get(
        ROWS_API,
        params={
            "dataset": DATASET,
            "config": SUBSET,
            "split": "train",
            "offset": offset,
            "length": count,
        },
        timeout=30,
    )
    response.raise_for_status()
    return parse_rows(response.json())
