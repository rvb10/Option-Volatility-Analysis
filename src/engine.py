
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.extract_inputs import get_inputs
from src.option_pricing import bs_price


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _year_fraction(d1, d2) -> float:
    return (d2 - d1).days / 365.0

def run_engine_df(trade_date_str: str = "2025-04-09"):
    inputs = get_inputs(trade_date_str)

    S0 = inputs["S0"]
    r = inputs["r"]
    q = inputs["q"]
    trade_date = inputs["trade_date"]
    expiry_date = inputs["expiry_date"]
    valuation_date = inputs["valuation_date"]
    K_put = inputs["K_put"]
    K_call = inputs["K_call"]
    iv_put_entry = inputs["iv_put_entry"]
    iv_call_entry = inputs["iv_call_entry"]
    contract_multiplier = inputs["contract_multiplier"]
    N_put = inputs["contracts_put_sold"]
    N_call = inputs["contracts_call_bought"]

    iv_put_val = iv_put_entry
    iv_call_val = iv_call_entry

    T_entry = _year_fraction(trade_date, expiry_date)
    T_val = _year_fraction(valuation_date, expiry_date)

    put_entry_px = bs_price(S0, K_put, T_entry, r, q, iv_put_entry, "put")
    call_entry_px = bs_price(S0, K_call, T_entry, r, q, iv_call_entry, "call")
    entry_cost = (-N_put * put_entry_px + N_call * call_entry_px) * contract_multiplier

    scenario_names = ["-15%", "-10%", "-5%", "0%", "+5%", "+10%", "+15%"]
    spot_multipliers = [0.85, 0.90, 0.95, 1.00, 1.05, 1.10, 1.15]

    rows = []
    for name, mult in zip(scenario_names, spot_multipliers):
        S_scn = S0 * mult
        put_val_px = bs_price(S_scn, K_put, T_val, r, q, iv_put_val, "put")
        call_val_px = bs_price(S_scn, K_call, T_val, r, q, iv_call_val, "call")
        mtm = (-N_put * put_val_px + N_call * call_val_px) * contract_multiplier
        pnl = mtm - entry_cost

        rows.append({
            "scenario": name,
            "spot_multiplier": mult,
            "S_val": S_scn,
            "put_val": put_val_px,
            "call_val": call_val_px,
            "mtm": mtm,
            "pnl": pnl,
        })

    scenarios_df = pd.DataFrame(rows)

    S_grid = np.linspace(0.6 * S0, 1.4 * S0, 161)
    payoff = (
        -N_put * np.maximum(K_put - S_grid, 0.0)
        + N_call * np.maximum(S_grid - K_call, 0.0)
    ) * contract_multiplier
    payoff_df = pd.DataFrame({"S_expiry": S_grid, "payoff": payoff})

    summary_df = pd.DataFrame({
        "Param": [
            "trade_date", "valuation_date", "expiry_date",
            "S0", "K_put", "K_call",
            "r", "q",
            "iv_put_entry", "iv_call_entry",
            "T_entry_years", "T_val_years",
            "entry_cost",
            "contracts_put_sold", "contracts_call_bought",
            "contract_multiplier",
        ],
        "Value": [
            trade_date.isoformat(),
            valuation_date.isoformat(),
            expiry_date.isoformat(),
            S0, K_put, K_call,
            r, q,
            iv_put_entry, iv_call_entry,
            T_entry, T_val,
            entry_cost,
            N_put, N_call,
            contract_multiplier,
        ],
    })

    return {
        "inputs": inputs,
        "summary_df": summary_df,
        "scenarios_df": scenarios_df,
        "payoff_df": payoff_df,
    }


def run_engine(trade_date_str: str = "2025-04-09") -> dict:
    root = _project_root()
    outputs_dir = root / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    results = run_engine_df(trade_date_str)

    summary_df = results["summary_df"]
    scenarios_df = results["scenarios_df"]
    payoff_df = results["payoff_df"]

    results_path = outputs_dir / "rr_results.xlsx"
    with pd.ExcelWriter(results_path, engine="openpyxl") as writer:
        summary_df.to_excel(writer, sheet_name="summary", index=False)
        scenarios_df.to_excel(writer, sheet_name="valuation_scenarios", index=False)
        payoff_df.to_excel(writer, sheet_name="expiry_payoff", index=False)

    plt.figure()
    plt.plot(scenarios_df["S_val"], scenarios_df["pnl"], marker="o")
    plt.xlabel("SPY spot at valuation date")
    plt.ylabel("PnL (USD)")
    plt.title("Risk-Reversal PnL (1 week before expiry)")
    plt.grid(True)
    plt.tight_layout()
    pnl_plot_path = outputs_dir / "pnl_valuation.png"
    plt.savefig(pnl_plot_path, dpi=140)
    plt.close()

    plt.figure()
    plt.plot(payoff_df["S_expiry"], payoff_df["payoff"])
    plt.xlabel("SPY spot at expiry")
    plt.ylabel("Payoff (USD)")
    plt.title("Expiry payoff (short 95% put, long 105% call)")
    plt.grid(True)
    plt.tight_layout()
    payoff_plot_path = outputs_dir / "payoff_expiry.png"
    plt.savefig(payoff_plot_path, dpi=140)
    plt.close()

    return {
        "excel_results": str(results_path),
        "pnl_plot": str(pnl_plot_path),
        "payoff_plot": str(payoff_plot_path),
    }


if __name__ == "__main__":
    paths = run_engine("2025-04-09")
    print("Generated files:")
    for k, v in paths.items():
        print(f"  {k}: {v}")
