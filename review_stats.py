"""Summary numbers for reviews saved during the current session."""


def review_summary(reviews):
    items = list(reviews)
    decided = [row for row in items if row.get("choice") in ("A", "B")]
    matches = sum(row.get("choice") == row.get("source_preferred") for row in decided)
    return {
        "saved": len(items),
        "decided": len(decided),
        "matches": matches,
        "agreement_percent": round(100 * matches / len(decided), 1) if decided else None,
    }
