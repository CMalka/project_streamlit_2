# Retail Analytics — Streamlit App

Interactive dashboard over the categories / products / customers / orders /
order_details dataset. Six tabs (Overview, Categories & Products, Customers,
Returns, Order Timing, Data Explorer), sidebar filters for date range /
category / region / segment that apply everywhere, and a plain-language
auto-generated summary at the bottom of every tab.

**This is a single self-contained file.** The five source tables are
embedded directly inside `app.py` as gzip+base64 blobs and decoded in
memory at startup — there's no `data/` folder, no relative paths, and
nothing else to commit. Just push `app.py` and `requirements.txt` to your
repo.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the URL Streamlit prints (usually http://localhost:8501).

## Deploying (e.g. Streamlit Community Cloud)

Point it at `app.py` as the main file — that's it. No data files to worry
about missing from the deploy.

## Notes

- Revenue = `Quantity * UnitPrice * (1 - DiscountRate)`; profit subtracts
  `Quantity * UnitCost`.
- `IsReturned` is treated as the source of truth for returns; the
  `9999-12-31` sentinel in `ReturnDate` is converted to a proper empty value.
- All charts are Plotly, so hovering shows exact values and every chart is
  zoomable/pannable.
- To swap in your own data later, replace the five `_..._B64` blobs at the
  top of `app.py` (gzip-compress + base64-encode your CSV and paste the
  string in), or change `load_data()` to read files/a database instead.
