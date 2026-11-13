import unittest
from unittest.mock import patch

from data_source import DATA_SOURCES, load_pairs, message_text, parse_rows


class DataSourceTests(unittest.TestCase):
    def test_reads_english_pair(self):
        sample = {
            "rows": [{
                "row_idx": 4,
                "row": {
                    "prompt": "How can I get better at drawing?",
                    "chosen": [
                        {"role": "user", "content": "How can I get better at drawing?"},
                        {"role": "assistant", "content": "Draw a little every day."},
                    ],
                    "rejected": [
                        {"role": "user", "content": "How can I get better at drawing?"},
                        {"role": "assistant", "content": "I'm not sure."},
                    ],
                },
            }],
        }
        rows = parse_rows(sample, "English · UltraFeedback")
        self.assertEqual(rows[0]["prompt"], "How can I get better at drawing?")
        self.assertEqual(rows[0]["chosen"], "Draw a little every day.")
        self.assertEqual(rows[0]["row_id"], 4)

    def test_reads_portuguese_pair(self):
        sample = {
            "rows": [{"row_idx": 7, "row": {
                "prompt": [{"role": "user", "content": "Oi, tudo bem?"}],
                "chosen": [{"role": "assistant", "content": "Tudo bem!"}],
                "rejected": [{"role": "assistant", "content": "Não."}],
            }}],
        }
        rows = parse_rows(sample, "Portuguese · GigaVerbo")
        self.assertEqual(rows[0]["prompt"], "Oi, tudo bem?")
        self.assertEqual(rows[0]["chosen"], "Tudo bem!")

    def test_drops_empty_and_identical_answers(self):
        sample = {"rows": [{"row_idx": 1, "row": {
            "prompt": "Question", "chosen": [{"role": "assistant", "content": "Same"}],
            "rejected": [{"role": "assistant", "content": "Same"}],
        }}]}
        self.assertEqual(parse_rows(sample, "English · UltraFeedback"), [])

    def test_message_text_only_assistant(self):
        messages = [{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi"}]
        self.assertEqual(message_text(messages, role="assistant"), "Hi")

    def test_rejects_bad_range(self):
        with self.assertRaises(ValueError):
            load_pairs("English · UltraFeedback", -1, 5)
        with self.assertRaises(ValueError):
            load_pairs("English · UltraFeedback", 0, 101)

    @patch("data_source.requests.get")
    def test_api_parameters_for_english(self, mock_get):
        mock_get.return_value.json.return_value = {"rows": []}
        load_pairs("English · UltraFeedback", 0, 5)
        args = mock_get.call_args.kwargs
        self.assertEqual(args["params"]["dataset"], DATA_SOURCES["English · UltraFeedback"]["dataset"])
        self.assertEqual(args["params"]["split"], "train_prefs")
        self.assertEqual(args["params"]["config"], "default")
        self.assertEqual(args["timeout"], 35)

    def test_invalid_payload(self):
        with self.assertRaises(ValueError):
            parse_rows({"error": "bad request"}, "English · UltraFeedback")


if __name__ == "__main__":
    unittest.main()
