# LLM Quality Lab

A small Python app to review LLM responses and compare human choices with a public preference dataset.

I work with AI evaluation and data quality, so I wanted to build a tool related to that work. The first version is simple: load real response pairs, review them without seeing the original label, and export the results.

## What it does

- Loads real prompts and response pairs from Hugging Face.
- Shows Response A and Response B in a blind review.
- Lets a reviewer choose A, B, Tie, or Not sure.
- Compares saved A/B decisions with the dataset's preference label.
- Exports the reviews as a CSV file.

There are no fake scores or pre-filled evaluations. Results only appear after someone reviews a pair.

## Data source

The app uses [GigaVerbo-v2 Preferences](https://huggingface.co/datasets/Polygl0t/gigaverbo-v2-preferences), published by Polygl0t. I start with the `harmless-no-reasoning` subset.

The original prompts and answers are in Portuguese. The app and documentation are in English.

One important point: the dataset labels were made through the dataset creators' generation and evaluation process. They are **not** a verified answer key or a set of independent human ratings. Agreement with the dataset is only one way to explore the data.

The dataset page lists an Apache 2.0 license. This project reads a small batch from the public Hugging Face Dataset Viewer API; it does not include the full dataset.

## Run the app

You need Python 3.10 or newer.

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app needs an internet connection to load the dataset.

## Run tests

```bash
python -m unittest discover -s tests -v
```

## Current limits

- This is an early version with one public dataset and one review screen.
- Reviews are kept in the current Streamlit session, not in a database. Export your CSV before closing the app.
- A small number of human decisions is not enough to make claims about a model's general performance.
- The app does not call an LLM API or score answers automatically.
- No private client data or internal evaluation guidelines are used.

## Next updates

I plan to add more review criteria, better filters, and a results page for saved evaluations. Later, I also want to work with English-language datasets.

---

Personal learning and portfolio project by Daniel Silva.
