# Economic Analysis Model (Simple path)

Interactive **Streamlit** port of the Excel workbook’s **Simple** analysis: scenario-weighted projections, combined revenue build-up, NPV-style metrics, and heuristic multiples. Core logic lives in `economics_model.py`; the UI is `app.py`.

**Live app (Streamlit):** [https://economic-analysis-model-n66hlcdqzg2vxhjwnrdnqr.streamlit.app/](https://economic-analysis-model-n66hlcdqzg2vxhjwnrdnqr.streamlit.app/)

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Tests

```bash
python -m pytest -q
```

## Publish to GitHub

This project is published as **`DhruvaPyapali/economic-analysis-model`** (the GitHub repository name **Economic Analysis Model** is represented without spaces as `economic-analysis-model`; you can set a friendlier **Description** in the repo settings on GitHub).

**Repository URL:** `https://github.com/DhruvaPyapali/economic-analysis-model`

Clone elsewhere:

```bash
git clone https://github.com/DhruvaPyapali/economic-analysis-model.git
cd economic-analysis-model
```

To push updates from this folder:

```bash
git add -A
git status
git commit -m "Describe your change"
git push origin main
```

Use `git add` selectively if you do not want to commit the large Excel/PDF files yet (`EconomicAnalysisModel-1.xlsm`, `EconomicAnalysisModelUserManual_v1-1.pdf`).

## GitHub Pages vs running the app

**GitHub Pages only serves static files** (HTML/CSS/JS). It **cannot** run a Python **Streamlit** server, so the app itself must be hosted elsewhere. This repo includes a **GitHub Pages** redirect from **`https://dhruvapyapali.github.io/economic-analysis-model/`** straight to the Streamlit app (see `docs/index.html`).

**Recommended:** deploy the Streamlit app with **[Streamlit Community Cloud](https://streamlit.io/cloud)** (free, connects to your GitHub repo).

1. Repo is on GitHub: **`DhruvaPyapali/economic-analysis-model`**.
2. Sign in at Streamlit Community Cloud and **New app** → pick **`economic-analysis-model`**.
3. Set **Main file path** to `app.py`.
4. Deploy; Streamlit assigns your app URL (this project: [live app](https://economic-analysis-model-n66hlcdqzg2vxhjwnrdnqr.streamlit.app/)).

The GitHub Pages URL redirects to the same Streamlit URL.

## Enable GitHub Pages (project site)

GitHub Pages is configured for this repo (**branch `main`**, folder **`/docs`**). The published URL **`https://dhruvapyapali.github.io/economic-analysis-model/`** immediately **redirects** to the live Streamlit app (GitHub cannot host Streamlit itself, so this is the usual pattern).

To change settings: repo **Settings** → **Pages** (exact URL is also shown there).

To point the redirect at a new Streamlit URL later, edit `docs/index.html` (search for `economic-analysis-model-n66hlcdqzg2vxhjwnrdnqr.streamlit.app`) and push.

## CI on every push

The workflow `.github/workflows/ci.yml` runs `pytest` on pushes and pull requests to `main`/`master`. It does not deploy Streamlit; it only validates the model tests.
