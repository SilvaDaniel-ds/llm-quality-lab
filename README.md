# LLM Quality Lab

A small web app to review real LLM responses and compare your own decisions with public preference labels.

I work with AI evaluation and data quality. I built this project to practice Python and look at real preference data outside of my regular work.

**Live app:** Add the Streamlit link here after this update is deployed.

## What you can do

- Open response pairs from public datasets.
- Review English examples from UltraFeedback, or switch to Portuguese examples from GigaVerbo.
- Compare Response A and Response B without seeing the original label first.
- Pick A, B, Tie, or Not sure. You can also add a reason and notes.
- Check your agreement with the dataset labels after saving a review.
- Export your reviews as a CSV file.

All numbers in the results section come from reviews saved in the current session. The app does not generate fake ratings or call a paid LLM API.

## Where the data comes from

**English (default):** [HuggingFaceH4 / UltraFeedback Binarized](https://huggingface.co/datasets/HuggingFaceH4/ultrafeedback_binarized) — `train_prefs` split. This dataset contains English-language prompts and response pairs. Its published preference labels come from an automated evaluation process based on UltraFeedback, **not a set of independent human votes**. The dataset page lists the MIT license.

**Portuguese (optional):** [Polygl0t / GigaVerbo-v2 Preferences](https://huggingface.co/datasets/Polygl0t/gigaverbo-v2-preferences) — `harmless-no-reasoning` subset. The published labels are also not a verified human answer key. The dataset page lists the Apache 2.0 license.

Both sources are loaded through the public [Hugging Face Dataset Viewer API](https://huggingface.co/docs/dataset-viewer/en/quick_start). I only fetch a small group of rows at a time. The datasets are not copied into this repository.

## Run it locally

Install Python 3.10+ and run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Tests:

```bash
python -m unittest discover -s tests -v
```

## Project files

- `app.py` — review page, UI, and CSV export
- `data_source.py` — datasets and row parsing
- `review_stats.py` — agreement calculations
- `.streamlit/config.toml` — app theme
- `tests/` — small checks for parsing and calculations

## A few things to know

- The source label is not necessarily the best answer. It is a useful comparison point, not a ground truth score.
- Your reviews are stored only in the current Streamlit browser session. Download the CSV if you want to keep them.
- The percentage shown is **agreement with the source labels**, not an accuracy measure for the models.
- A few reviews are not enough to draw broad conclusions about model performance.
- The app does not use private company data or internal evaluation guidelines.

## Changes

- **v0.1:** First review screen with public Portuguese data.
- **v0.2:** Added English response pairs, kept Portuguese as an option, and redesigned the interface for easier reading.

This is an independent learning and portfolio project by Daniel Silva.
