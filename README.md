# Retail Analytics — Streamlit App

Interactive dashboard over `categories.csv`, `products.csv`, `customers.csv`,
`orders.csv`, and `order_details.csv`. Six tabs (Overview, Categories &
Products, Customers, Returns, Order Timing, Data Explorer), sidebar filters
for date range / category / region / segment that apply everywhere, and a
plain-language auto-generated summary at the bottom of every tab.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the URL Streamlit prints (usually http://localhost:8501).

## Folder layout

```
app.py
requirements.txt
data/
  categories.csv
  products.csv
  customers.csv
  orders.csv
  order_details.csv
```

The app reads the CSVs from `./data/` by relative path — keep that folder
next to `app.py`, or edit the paths in `load_data()` in `app.py` if you want
to point it elsewhere.

## Notes

- Revenue = `Quantity * UnitPrice * (1 - DiscountRate)`; profit subtracts
  `Quantity * UnitCost`.
- `IsReturned` is treated as the source of truth for returns; the
  `9999-12-31` sentinel in `ReturnDate` is converted to a proper empty value.
- All charts are Plotly, so hovering shows exact values and every chart is
  zoomable/pannable.
