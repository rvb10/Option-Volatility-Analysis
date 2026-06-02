import sys
from pathlib import Path
from datetime import date
import io

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]  
SRC_DIR = PROJECT_ROOT / "src"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

sys.path.append(str(SRC_DIR))

from src.engine import run_engine_df   

st.set_page_config(page_title="SPY 1M Risk Reversal", layout="wide")

st.title("SPY 1-Month Risk-Reversal Trade Analyzer")
st.write("Short 95% put, long 105% call — scenario PnL one week before expiry.")

st.sidebar.header("Configuration")

default_trade_date = date(2025, 4, 9)
trade_date = st.sidebar.date_input("Trade Date", value=default_trade_date)

run_button = st.sidebar.button("Run Analysis")

st.sidebar.markdown("---")
st.sidebar.markdown("**Data files expected in** `data/raw/`:")
st.sidebar.code("Index Data.xlsx\nIV.xlsx\noptions_parsed.xlsx")

if run_button:
    trade_date_str = trade_date.strftime("%Y-%m-%d")

    try:
        results = run_engine_df(trade_date_str)
    except Exception as e:
        st.error(f"Error running engine: {e}")
    else:
        inputs = results["inputs"]
        summary_df = results["summary_df"]
        scenarios_df = results["scenarios_df"]
        payoff_df = results["payoff_df"]

        st.subheader("Trade Snapshot")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Spot S₀", f"{inputs['S0']:.2f}")
        col2.metric("r (SOFR)", f"{inputs['r']*100:.2f}%")
        col3.metric("q (Dividend Yield)", f"{inputs['q']*100:.2f}%")
        entry_cost_val = float(
            summary_df.loc[summary_df["Param"] == "entry_cost", "Value"].iloc[0]
        )
        col4.metric("Entry Cost (USD)", f"{entry_cost_val:,.2f}")

        col5, col6, col7 = st.columns(3)
        col5.metric("Put Strike (95%)", f"{inputs['K_put']:.2f}")
        col6.metric("Call Strike (105%)", f"{inputs['K_call']:.2f}")
        col7.metric(
            "Structure",
            f"{inputs['contracts_put_sold']} short puts / {inputs['contracts_call_bought']} long calls",
        )

        st.markdown("---")

        st.subheader("PnL Scenarios (1 Week Before Expiry)")
        st.dataframe(
            scenarios_df[["scenario", "S_val", "pnl", "mtm", "put_val", "call_val"]],
            use_container_width=True,
        )

        st.subheader("PnL vs SPY Spot at Valuation Date")
        fig1, ax1 = plt.subplots()
        ax1.plot(scenarios_df["S_val"], scenarios_df["pnl"], marker="o")
        ax1.set_xlabel("SPY spot at valuation date")
        ax1.set_ylabel("PnL (USD)")
        ax1.set_title("Risk-Reversal PnL (1 week before expiry)")
        ax1.grid(True)
        st.pyplot(fig1)

        st.subheader("Expiry Payoff Profile")
        fig2, ax2 = plt.subplots()
        ax2.plot(payoff_df["S_expiry"], payoff_df["payoff"])
        ax2.set_xlabel("SPY spot at expiry")
        ax2.set_ylabel("Payoff (USD)")
        ax2.set_title("Expiry payoff (short 95% put, long 105% call)")
        ax2.grid(True)
        st.pyplot(fig2)

        with st.expander("Show full parameter summary"):
            st.dataframe(summary_df, use_container_width=True)

        st.subheader("Download Results")

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            summary_df.to_excel(writer, sheet_name="summary", index=False)
            scenarios_df.to_excel(writer, sheet_name="valuation_scenarios", index=False)
            payoff_df.to_excel(writer, sheet_name="expiry_payoff", index=False)
        buffer.seek(0)

        st.download_button(
            label="Download Excel Results",
            data=buffer,
            file_name=f"SPY_RR_results_{trade_date_str}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

else:
    st.info("Set the trade date in the sidebar and click **Run Analysis** to generate results.")
