"""Small calculations for saved human reviews."""


def review_summary(reviews):
    saved = list(reviews)
    decided = [item for item in saved if item["choice"] in ("A", "B")]
    matches = sum(item["choice"] == item["source_preferred"] for item in decided)

    return {
        "saved": len(saved),
        "decided": len(decided),
        "matches": matches,
        "agreement_percent": round(100 * matches / len(decided), 1) if decided else None,
    }
