
# Tariff & Supply Chain Scenario Copilot (Streamlit)

An interactive demo to model tariff/FX scenarios over a SKU list, see landed cost impact, and get simple supplier-country switch recommendations.

## What it does
- Upload a SKU CSV (sku, product_name, base_cost, supplier_country, hs_code, annual_units)
- Adjust per-country tariff rates and a global FX multiplier
- See baseline vs scenario annual costs, top cost increases, spend share by country
- Get rule-based recommendations for alternate supplier countries

## Quickstart (local)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```
Then open the local URL printed in the terminal.

## Deploy
- Streamlit Community Cloud: one-click from repo
- Render / Railway: use `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`

## Notes
- Demo rates are placeholders. Replace with authoritative tariff tables and constraints.
- Extend with lead-time risk, MOQ, quality score, and multi-currency per supplier.
