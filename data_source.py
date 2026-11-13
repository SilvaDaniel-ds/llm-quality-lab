"""Load public preference pairs from the Hugging Face Dataset Viewer."""

import requests

API_URL = "https://datasets-server.huggingface.co/rows"

DATA_SOURCES = {
    "English · UltraFeedback": {
        "dataset": "HuggingFaceH4/ultrafeedback_binarized",
        "config": "default",
        "split": "train_prefs",
        "language": "English",
        "label_note": "Dataset preference based on automated model ratings, not human ground truth.",
    },
    "Portuguese · GigaVerbo": {
        "dataset": "Polygl0t/gigaverbo-v2-preferences",
        "config": "harmless-no-reasoning",
        "split": "train",
        "language": "Portuguese",
        "label_note": "Dataset preference is not verified human ground truth.",
    },
}


def source_link(source):
    return "https://huggingface.co/datasets/" + DATA_SOURCES[source]["dataset"]


def message_text(messages, role=None):
    """Return non-empty text from chat messages, keeping the original order."""
    if not isinstance(messages, list):
        return ""

    pieces = []
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        if role is not None and msg.get("role") != role:
            continue
        content = msg.get("content")
        if isinstance(content, str) and content.strip():
            pieces.append(content.strip())
    return "\n\n".join(pieces)


def parse_rows(payload, source):
    """Use the real row index as the ID. No placeholder records."""
    if source not in DATA_SOURCES:
        raise ValueError("Unknown data source")
    if not isinstance(payload, dict) or not isinstance(payload.get("rows"), list):
        raise ValueError("Unexpected dataset response")

    is_english = source == "English · UltraFeedback"
    results = []
    for record in payload["rows"]:
        if not isinstance(record, dict) or not isinstance(record.get("row"), dict):
            continue
        row = record["row"]
        row_id = record.get("row_idx")

        if is_english:
            prompt = row.get("prompt", "")
            chosen = message_text(row.get("chosen"), role="assistant")
            rejected = message_text(row.get("rejected"), role="assistant")
        else:
            prompt = message_text(row.get("prompt"))
            chosen = message_text(row.get("chosen"), role="assistant") or message_text(row.get("chosen"))
            rejected = message_text(row.get("rejected"), role="assistant") or message_text(row.get("rejected"))

        if not isinstance(prompt, str) or not prompt.strip():
            continue
        if not chosen or not rejected or chosen == rejected or not isinstance(row_id, int):
            continue

        results.append({
            "row_id": row_id,
            "prompt": prompt.strip(),
            "chosen": chosen,
            "rejected": rejected,
        })
    return results


def load_pairs(source, offset=0, count=10):
    if source not in DATA_SOURCES:
        raise ValueError("Unknown data source")
    if not isinstance(offset, int) or offset < 0 or not isinstance(count, int) or not 1 <= count <= 100:
        raise ValueError("Offset or row count is out of range")

    settings = DATA_SOURCES[source]
    response = requests.get(
        API_URL,
        params={
            "dataset": settings["dataset"],
            "config": settings["config"],
            "split": settings["split"],
            "offset": offset,
            "length": count,
        },
        timeout=35,
    )
    response.raise_for_status()
    return parse_rows(response.json(), source)
