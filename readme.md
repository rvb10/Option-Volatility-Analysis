# SPY 1M Risk-Reversal Scenario Analysis

## Task 1

This project analyzes a 1-month SPY **risk-reversal** trade as of **2025-04-09**:

* **Base trade**:

  * Short 95% moneyness SPY put (1-month)
  * Long 105% moneyness SPY call (1-month)
  * 1000 contracts each, 100x multiplier

It includes:

* A Black–Scholes–Merton option pricing module with dividend yield
* A scenario engine for P&L one week before expiry
* Expiry payoff profiles
* Historical analysis for IV, realized vol, VRP, and skew
* Bonus analysis for:

  * A **put-spread + call** structure (short 95% put, long 90% put, long 105% call)
  * Comparison with buying SPY outright on equivalent notional

---


* Python **3.9+** (3.10/3.11/3.12 are fine)
* `pip` (or `pip3`)
* (Optional) [`virtualenv`](https://virtualenv.pypa.io/) or `python -m venv`
* Excel reader dependencies are handled via `requirements.txt` (`pandas`, `openpyxl`, etc.)

---


From the project root (`LH Pamli Project/`):

```bash
# 1. Create a virtual environment (recommended)
python -m venv .venv

# 2. Activate it
# macOS / Linux:
source .venv/bin/activate

# Windows (PowerShell):
# .venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt
```

If you ever want to check what’s installed:

```bash
pip list
```

---


 The following data files are in `data/raw/`:

1. **Index Data.xlsx**

   * Contains SPY close, VIX close, SOFR, ex-dates, dividend amounts, implied dividend yield.
   * The code uses:

     * SPY closing prices
     * SOFR (risk-free proxy)
     * Implied dividend yield (continuous yield `q`)

2. **IV.xlsx**

   * Columns (daily):

     * `Date`
     * `SPY Close`
     * `ATM Vol 1m`
     * `95% Moneyness Vol 1m`
     * `105% Moneyness Vol 1m`

3. **options_parsed.xlsx**

   * Columns:

     * `Type`, `ID_BB_SEC_NUM_DES`, `Mid Price`, `Delta`, `Gamma`, `Vega`, `Theta`, `IV`, `ticker`, `expiry`, `option_type`, `strike`
   * Contains at least:

     * 1M SPY 95% put
     * 1M SPY 105% call




### `src/option_pricing.py`

Implements Black–Scholes–Merton with continuous dividend yield:

* `bs_price(S, K, T, r, q, sigma, option_type)`
* `bs_delta`, `bs_gamma`, `bs_vega`, `bs_theta`

All rates/vols are **annualized decimals**, `T` is in years.

You can do a quick sanity check:

```bash
python -c "from src.option_pricing import bs_price; print(bs_price(500, 480, 1/12, 0.05, 0.015, 0.24, 'call'))"
```

---

### `src/extract_inputs.py`

Reads all raw Excel files and returns a consolidated input dictionary for a given trade date.

```python
from src.extract_inputs import get_inputs

inputs = get_inputs("2025-04-09")
print(inputs)
```

Typical keys:

* `S0` – SPY spot on trade date
* `r` – annualized risk-free rate from SOFR
* `q` – annualized implied dividend yield
* `trade_date`, `expiry_date`, `valuation_date` (1 week before expiry)
* `K_put`, `K_call` – 95% and 105% strikes
* `iv_put_entry`, `iv_call_entry` – entry IVs
* `contracts_put_sold`, `contracts_call_bought`
* `contract_multiplier` (100)

---

### `src/engine.py` – Risk-Reversal Scenario Engine

Runs scenario analysis for the base trade (short 95% put, long 105% call).

#### In-memory usage (for notebooks):

```python
from src.engine import run_engine_df

results = run_engine_df("2025-04-09")
summary_df    = results["summary_df"]
scenarios_df  = results["scenarios_df"]   # PnL 1 week before expiry
payoff_df     = results["payoff_df"]      # expiry payoff profile

print(summary_df)
print(scenarios_df)
```

#### File-output usage (Excel + PNG charts):

```bash
python -m src.engine
```

This writes to `outputs/`:

* `rr_results.xlsx`
* `pnl_valuation.png`
* `payoff_expiry.png`


---

## Running the Streamlit App 

```bash
streamlit run app.py
```

From the project root. The app will typically let you:

* Run the scenario engine
* View summary, scenario table, and payoff charts interactively

---
## Task 2
Vol and Skew Analysis (iv_analysis.ipynb)

This notebook provides the empirical justification for:

Selling rich downside skew,

Being cautious about shorting volatility when VRP is extremely low.

## Bonus Task

For deeper analysis (put-spread, SPY comparison, historical stats):

1. Start Jupyter from the project root:

```bash
jupyter notebook
# or
jupyter lab
```

Just run the bonus.ipynb file for the bonus work analysis

---

## Troubleshooting

* **`ModuleNotFoundError: No module named 'src'`**
  Make sure you:

  * Run Python / Jupyter from the project root, and
  * Append the root to `sys.path`:

    ```python
    import sys
    from pathlib import Path
    sys.path.append(str(Path(".").resolve()))
    ```

* **Excel reading errors**
  Check:

  * Filenames match exactly (`Index Data.xlsx`, `IV.xlsx`, `options_parsed.xlsx`)
  * Sheets have the expected columns

* **Plots not appearing**
  In notebooks, add:

  ```python
  %matplotlib inline
  ```

---

