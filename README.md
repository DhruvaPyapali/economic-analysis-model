# Economic Analysis Model (Simple path)

Interactive **Streamlit** port of the Excel workbook’s **Simple** analysis: scenario-weighted projections, combined revenue build-up, NPV-style metrics, and heuristic multiples. Core logic lives in `economics_model.py`; the UI is `app.py`.

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

This project is published as **`DhruvaPyapali/CodersRepo`**.

**Repository URL:** `https://github.com/DhruvaPyapali/CodersRepo`

To push updates from this folder:

```bash
git add -A
git status
git commit -m "Describe your change"
git push origin main
```

Add `EconomicAnalysisModel-1.xlsm` and the PDF only if you want them in the repo (they are large).

## GitHub Pages vs running the app

**GitHub Pages only serves static files** (HTML/CSS/JS). It **cannot** run a Python **Streamlit** server, so the app itself must be hosted elsewhere. This repo includes a small **static site** under `docs/` that you can publish on Pages as a project homepage (instructions + link to the live app).

**Recommended:** deploy the Streamlit app with **[Streamlit Community Cloud](https://streamlit.io/cloud)** (free, connects to your GitHub repo).

1. Push this repo to GitHub.
2. Sign in at Streamlit Community Cloud and **New app** → pick the repo.
3. Set **Main file path** to `app.py`.
4. Deploy; Streamlit will assign a URL (you can often choose a subdomain). It will look like `https://<your-chosen-name>.streamlit.app`.

Then edit `docs/index.html`: set the `Open live app` link (`id="app-link"`) `href` to that Streamlit URL, commit, and push again.

## Enable GitHub Pages (project site)

1. Repo **Settings** → **Pages**.
2. **Build and deployment**: **Deploy from a branch**.
3. Branch **main**, folder **`/docs`**, save.
4. After a minute, the project site is at **`https://dhruvapyapali.github.io/CodersRepo/`** (the exact URL is also shown on the Pages settings screen).

The `docs/index.html` page is a landing site only; the interactive model runs on Streamlit Cloud (or any other host you prefer).

## CI on every push

The workflow `.github/workflows/ci.yml` runs `pytest` on pushes and pull requests to `main`/`master`. It does not deploy Streamlit; it only validates the model tests.
