import unittest

from review_stats import review_summary


class ReviewStatsTests(unittest.TestCase):
    def test_no_reviews(self):
        self.assertEqual(review_summary([])["agreement_percent"], None)

    def test_one_different_choice(self):
        summary = review_summary([{"choice": "B", "source_preferred": "A"}])
        self.assertEqual(summary["saved"], 1)
        self.assertEqual(summary["matches"], 0)
        self.assertEqual(summary["agreement_percent"], 0.0)

    def test_only_ab_choices_are_counted(self):
        reviews = [
            {"choice": "B", "source_preferred": "B"},
            {"choice": "A", "source_preferred": "B"},
            {"choice": "Tie", "source_preferred": "A"},
            {"choice": "Not sure", "source_preferred": "B"},
        ]
        self.assertEqual(review_summary(reviews)["agreement_percent"], 50.0)
        self.assertEqual(review_summary(reviews)["decided"], 2)


if __name__ == "__main__":
    unittest.main()
