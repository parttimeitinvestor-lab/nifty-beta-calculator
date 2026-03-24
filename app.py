import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Beta Hedge Calculator | Part Time IT Investor", layout="wide", page_icon="📈")

# --- HIDE STREAMLIT BRANDING & GITHUB LINK ---
hide_st_style = """
            <style>
            /* 1. Target ONLY the GitHub link in the header and hide it */
            header a[href*="github.com"] {display: none !important;}
            
            /* 2. Hide the 'Fork' and 'Star' toolbar if it appears */
            [data-testid="stToolbar"] {display: none !important;}

            /* 3. Hide the Deploy and Manage buttons */
            [data-testid="stAppDeployButton"] {display: none !important;}
            [data-testid="manage-app-button"] {display: none !important;}
            
            /* 4. Hide the standard footer and viewer badge */
            footer {display: none !important;}
            [data-testid="stViewerBadge"] {display: none !important;}
            .viewerBadge_container {display: none !important;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)


# --- MAIN PAGE: HEADER ---
col1, col2 = st.columns([1, 6])

with col1:
    try:
        st.image("logo.PNG", use_column_width=True) 
    except:
        pass 

with col2:
    st.title("🛡️ Portfolio Beta & Option Hedge Calculator")
    st.markdown("**Developed by Part Time IT Investor**")

# This creates a full-width red button right under the title on mobile and desktop
youtube_link = "https://www.youtube.com/channel/UCl1-Z3vCL3zUNjlLlT_Lsxg" 
st.markdown(
    f"""
    <a href="{youtube_link}" target="_blank" style="text-decoration: none;">
        <div style="background-color:#FF0000;color:white;padding:12px;text-align:center;border-radius:5px;font-weight:bold;font-size:16px;margin-bottom:20px;">
            📺 Subscribe to Part Time IT Investor on YouTube
        </div>
    </a>
    """,
    unsafe_allow_html=True
)

st.markdown("""
Calculate your exact portfolio risk and find out how many put options you need to hedge against a market crash.
""")

st.markdown("---")

# --- NEW: HEDGING PARAMETERS (Moved from Sidebar to Main Page) ---
st.subheader("⚙️ Hedging Parameters")

# The Subscriber-Only Gate
with st.expander("🔐 Unlock Advanced Strategies"):
    passcode = st.text_input("Enter Subscriber Passcode", type="password")
    if passcode == "NIFTY2026": 
        st.success("Advanced Mode Active!")
        hedge_mode = st.radio("Hedge Strategy", ["Buy Puts (Insurance)", "Sell Call Spreads (Income)"])
    else:
        st.info("Advanced strategies are locked. Watch the video to find the code!")
        hedge_mode = "Buy Puts (Insurance)"

# Using 3 columns so the inputs look compact and professional on Desktop, but stack neatly on Mobile
param_col1, param_col2, param_col3 = st.columns(3)

with param_col1:
    index_symbol = st.text_input("Index Symbol", value="^NSEI", help="^NSEI is Nifty 50")
with param_col2:
    lot_size = st.number_input("Index Lot Size", value=50, step=1)
with param_col3:
    if hedge_mode == "Buy Puts (Insurance)":
        target_delta = st.number_input("Target Put Delta", value=0.20, step=0.05, help="0.20 is a standard OTM Put.")
        mode_label = "PUTS"
    else:
        target_delta = st.number_input("Net Strategy Delta", value=0.25, step=0.05, help="The net delta of your Call Spread.")
        mode_label = "CALL SPREADS"

st.markdown("---")

# --- MAIN PAGE: PORTFOLIO INPUT ---
#st.subheader("Step 1: Enter Your Portfolio")

# --- CORE LOGIC ---
@st.cache_data(ttl=300) # Fix 1: Cache refreshes every 5 mins instead of 1 hour
def fetch_yf_data(ticker, days=365):
    try:
        # Fix 2: Use period="1y" to force the library to grab today's live intraday price
        data = yf.download(ticker, period="1y", progress=False)
        
        if data is None or data.empty:
            return pd.Series(dtype=float)
        
        # Safely extract close prices to avoid single-day array crashes
        closes = data['Close']
        if isinstance(closes, pd.DataFrame):
            closes = closes.iloc[:, 0]
            
        # Fix 3: Drop NaNs just in case the live intraday candle hasn't fully formed
        return pd.Series(closes).dropna()
        
    except Exception:
        return pd.Series(dtype=float)
# --- NIFTY 50 LIST ---
nifty50_symbols = [
    "ADANIENT", "ADANIPORTS", "APOLLOHOSP", "ASIANPAINT", "AXISBANK",
    "BAJAJ-AUTO", "BAJFINANCE", "BAJAJFINSV", "BEL", "BPCL",
    "BHARTIARTL", "BRITANNIA", "CIPLA", "COALINDIA", "DIVISLAB",
    "DRREDDY", "EICHERMOT", "GRASIM", "HCLTECH", "HDFCBANK",
    "HDFCLIFE", "HEROMOTOCO", "HINDALCO", "HINDUNILVR", "ICICIBANK",
    "ITC", "INDUSINDBK", "INFY", "JSWSTEEL", "KOTAKBANK",
    "LTIM", "LT", "M&M", "MARUTI", "NTPC",
    "NESTLEIND", "ONGC", "POWERGRID", "RELIANCE", "SBILIFE",
    "SBIN", "SUNPHARMA", "TCS", "TATACONSUM", "TATAMOTORS",
    "TATASTEEL", "TECHM", "TITAN", "TRENT", "WIPRO"
]

# --- MAIN PAGE: PORTFOLIO INPUT ---
st.subheader("Step 1: Enter Your Portfolio")

tab1, tab2 = st.tabs(["✍️ Nifty 50 Grid", "📁 Upload Zerodha File"])

holdings_list = []

with tab1:
    st.markdown("Scroll through the Nifty 50 stocks below. Just enter your **Quantity** and **Average Price** for the ones you own. You can add new rows at the bottom.")
    
    default_df = pd.DataFrame({
        "Symbol": nifty50_symbols,
        "Quantity": [0.0] * 50,
        "Average Price": [0.0] * 50
    })
    
    edited_df = st.data_editor(default_df, num_rows="dynamic", use_container_width=True, height=400)
    
    if st.button("Calculate Hedge from Grid", type="primary"):
        for index, row in edited_df.iterrows():
            sym = str(row["Symbol"]).strip()
            try:
                qty = float(row["Quantity"])
                avg_price = float(row["Average Price"])
            except ValueError:
                continue 
                
            if sym and qty > 0:
                yf_sym = sym if sym.endswith(".NS") or sym.endswith(".BO") else f"{sym}.NS"
                holdings_list.append({
                    "Symbol": sym,
                    "YF_Ticker": yf_sym,
                    "Qty": qty,
                    "Pledged": 0, 
                    "Avg Price": avg_price
                })

with tab2:
    st.markdown("Download your holdings from the Zerodha Console (CSV or Excel) and upload it directly here.")
    uploaded_file = st.file_uploader("Upload Zerodha Holdings (.csv or .xlsx)", type=["csv", "xlsx"], key="zerodha_upload")
    
    if st.button("Calculate Hedge from File", type="primary"):
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith('.csv'):
                    raw_df = pd.read_csv(uploaded_file, header=None)
                else:
                    raw_df = pd.read_excel(uploaded_file, header=None)
                
                header_idx = -1
                for i, row in raw_df.iterrows():
                    row_vals = [str(val).strip().lower() for val in row.values]
                    if 'symbol' in row_vals or 'instrument' in row_vals:
                        header_idx = i
                        break
                
                if header_idx == -1:
                    st.error("Error: Could not find a 'Symbol' or 'Instrument' row to use as headers.")
                else:
                    df = raw_df.iloc[header_idx + 1:].copy()
                    df.columns = [str(c).strip() for c in raw_df.iloc[header_idx]]
                    
                    sym_col = 'Symbol' if 'Symbol' in df.columns else 'Instrument'
                    price_col = 'Average Price' if 'Average Price' in df.columns else ('Avg. cost' if 'Avg. cost' in df.columns else None)
                    
                    # Fix 1: Sum all Qty columns EXCEPT 'Long Term' to prevent double counting
                    qty_cols = [c for c in df.columns if (c == 'Qty.' or str(c).startswith('Quantity')) and 'long term' not in str(c).lower()]
                    
                    # Fix 2: Dynamically find all Pledged columns (Margin + MTF) for the UI display
                    pledged_cols = [c for c in df.columns if 'pledged' in str(c).lower()]

                    if price_col and qty_cols:
                        for index, row in df.iterrows():
                            sym = str(row[sym_col]).strip()
                            if not sym or str(sym).lower() == 'nan': 
                                continue
                                
                            price_val = pd.to_numeric(row[price_col], errors='coerce')
                            qty_val = pd.to_numeric(row[qty_cols], errors='coerce').sum()

                            if pd.notna(price_val) and qty_val > 0:
                                clean_sym = sym
                                if clean_sym.endswith('-E') or clean_sym.endswith('-F') or clean_sym.endswith('-GS'):
                                    clean_sym = clean_sym.rsplit('-', 1)[0]
                                    
                                yf_sym = clean_sym if clean_sym.endswith(".NS") or clean_sym.endswith(".BO") else f"{clean_sym}.NS"
                                
                                # Accurately capture pledged quantity for the UI
                                pledged_val = pd.to_numeric(row[pledged_cols], errors='coerce').sum() if pledged_cols else 0

                                holdings_list.append({
                                    "Symbol": sym,
                                    "YF_Ticker": yf_sym,
                                    "Qty": qty_val,
                                    "Pledged": pledged_val,
                                    "Avg Price": float(price_val)
                                })
                    else:
                        st.error("Found the symbol column, but couldn't identify the Quantity or Price columns.")
            except Exception as e:
                st.error(f"Error reading file: {e}")
        else:
            st.warning("Please upload a file first.")

# --- PROCESSING & RESULTS ---
if holdings_list:
    st.markdown("---")
    with st.spinner(f"Fetching 1 year of data for {len(holdings_list)} stocks and calculating Beta matrix..."):
        
        index_closes = fetch_yf_data(index_symbol)
        if index_closes.empty:
            st.error(f"Could not fetch index data for {index_symbol}. Check the symbol.")
            st.stop()
            
        index_returns = index_closes.pct_change().dropna()
        index_var = np.var(index_returns)
        index_ltp = float(index_closes.iloc[-1])

        total_invested = 0
        total_current_value = 0
        portfolio_beta = 0
        
        for item in holdings_list:
            stock_closes = fetch_yf_data(item['YF_Ticker'])
            qty = item['Qty']
            avg_price = item['Avg Price']
            invested = qty * avg_price
            
            # Robust fallback for bonds, delisted ETFs, or missing data
            if not isinstance(stock_closes, pd.Series) or stock_closes.empty or len(stock_closes) < 2:
                item['LTP'] = avg_price
                item['P&L'] = 0.0
                item['Beta'] = 0.0 # Bonds/Missing assets have 0 equity risk
                item['Current Value'] = invested
                
                total_invested += invested
                total_current_value += invested
                continue
            
            ltp = float(stock_closes.iloc[-1])
            current = qty * ltp
            
            total_invested += invested
            total_current_value += current
            
            stock_returns = stock_closes.pct_change().dropna()
            aligned_data = pd.concat([stock_returns, index_returns], axis=1, keys=['stock', 'index']).dropna()
            
            if len(aligned_data) > 30:
                covar = np.cov(aligned_data['stock'], aligned_data['index'])[0, 1]
                stock_beta = covar / index_var
            else:
                stock_beta = 1.0
            
            item['LTP'] = ltp
            item['P&L'] = current - invested
            item['Beta'] = stock_beta
            item['Current Value'] = current

        if total_current_value == 0:
            st.error("Total portfolio value calculated as zero. Check your inputs.")
            st.stop()
            
        for item in holdings_list:
            if 'Beta' in item and item['Current Value'] > 0:
                weight = item['Current Value'] / total_current_value
                portfolio_beta += (weight * item['Beta'])

        # --- NEW: VOLATILITY-ADJUSTED BETA (CRASH MODE) ---
        with st.spinner("Fetching India VIX for Crash Detection..."):
            vix_closes = fetch_yf_data("^INDIAVIX")
            if not vix_closes.empty:
                current_vix = float(vix_closes.iloc[-1])
                baseline_vix = 15.0 # Standard "normal" volatility for India
                
                # Only inflate Beta if VIX is above normal (Crash Scenario)
                if current_vix > baseline_vix:
                    vix_scalar = current_vix / baseline_vix
                    adjusted_portfolio_beta = portfolio_beta * vix_scalar
                    vix_status = f"CRASH MODE ACTIVE (VIX: {current_vix:.2f})"
                else:
                    adjusted_portfolio_beta = portfolio_beta
                    vix_status = f"NORMAL VOLATILITY (VIX: {current_vix:.2f})"
            else:
                adjusted_portfolio_beta = portfolio_beta
                vix_status = "VIX DATA UNAVAILABLE"

        # Use the adjusted beta for the final math
        beta_weighted_value = total_current_value * adjusted_portfolio_beta
        exact_contracts = beta_weighted_value / (index_ltp * lot_size * target_delta)
        recommended_contracts = round(exact_contracts)

        st.success("Analysis Complete!")
        
        # The Bold Risk Statement 
        st.markdown(f"### 🚨 **Risk Analysis: If Nifty 50 falls by 1%, your portfolio is expected to fall by {adjusted_portfolio_beta:.2f}%**")
        st.caption(f"🛡️ **Volatility Sensor:** {vix_status}")
        st.success("Analysis Complete!")

       # --- NEW: ASK GEMINI AI VIBE SECTION ---
        st.markdown("---")
        with st.expander("🤖 **Ask Gemini: What do you think of my portfolio?**"):
            st.write("🔍 **Scanning Beta exposure...**")
            
            # The logic remains exactly the same
           # The corrected logic
            if adjusted_portfolio_beta > 1.2:
                sentiment = "Aggressive/High Risk"
                advice = "Your portfolio is highly sensitive to market swings. While you'll outperform in a bull run, a Nifty correction will hit you harder than most. Hedging is strongly advised."
            elif adjusted_portfolio_beta < 0.8:
                sentiment = "Defensive/Conservative"
                advice = "You are well-insulated from market volatility. Your assets move less than the index, but you might lag behind during a massive market rally."
            else:
                sentiment = "Market Neutral/Balanced"
                advice = "Your portfolio is perfectly synced with the Nifty 50. You are capturing the broad market move efficiently."

            st.markdown(f"### **Gemini's AI Insights**")
            st.write(f"**Portfolio Stance:** {sentiment}")
            st.write(f"**AI Observation:** {advice}")
            st.write("---")
            st.caption("Powered by Gemini. Built by Part Time IT Investor.")
        
        # --- DYNAMIC TERMINAL LABELS (Adapts to Insurance vs Income mode) ---
        try:
            current_mode = hedge_mode
        except NameError:
            current_mode = "Buy Puts (Insurance)" # Fallback safety

        if current_mode == "Buy Puts (Insurance)":
            exact_lbl = "Exact Puts Required:"
            final_action = "BUY"
            final_asset = "LOTS OF PUTS"
            delta_lbl = "Option Delta Used:"
        else:
            exact_lbl = "Exact Spreads Required:"
            final_action = "CREATE"
            final_asset = "LOTS OF BEAR CALL SPREADS"
            delta_lbl = "Strategy Net Delta:"

        # --- BUILD THE RAW ASCII TERMINAL OUTPUT ---
        out_str = "-" * 85 + "\n"
        out_str += f"{'SYMBOL':<15} | {'QTY':<6} | {'PLEDGED':<7} | {'AVG PRICE':<9} | {'LTP':<9} | {'P&L':<10} | {'BETA'}\n"
        out_str += "-" * 85 + "\n"
        
        for item in holdings_list:
            sym = item['Symbol']
            qty = item['Qty']
            pledged = item.get('Pledged', 0) 
            avg_price = item['Avg Price']
            ltp = item.get('LTP', 0.0)
            pnl = item.get('P&L', 0.0)
            beta = item.get('Beta', 0.0)
            
            out_str += f"{sym:<15} | {qty:<6.0f} | {pledged:<7.0f} | {avg_price:<9.2f} | {ltp:<9.2f} | {pnl:<10.2f} | {beta:.2f}\n"

        out_str += "-" * 85 + "\n\n\n"
        
        out_str += "=" * 55 + "\n"
        out_str += "LIVE HEDGE CALCULATION REPORT\n"
        out_str += "=" * 55 + "\n"
        out_str += f"Total Invested Value:        Rs {total_invested:,.2f}\n"
        out_str += f"Total Live Portfolio Value:  Rs {total_current_value:,.2f}\n"
        out_str += f"Total Portfolio P&L:         Rs {(total_current_value - total_invested):,.2f}\n"
        out_str += "-" * 55 + "\n"
        out_str += f"Weighted Portfolio Beta:     {portfolio_beta:.2f}\n"
        out_str += f"Beta-Weighted Risk Exposure: Rs {beta_weighted_value:,.2f}\n"
        out_str += "-" * 55 + "\n"
        out_str += f"Current Index Price:         Rs {index_ltp:,.2f} ({index_symbol})\n"
        out_str += f"{delta_lbl:<28} {target_delta}\n"
        out_str += "-" * 55 + "\n"
        out_str += f"{exact_lbl:<28} {exact_contracts:.2f}\n"
        out_str += f"> FINAL CALCULATED HEDGE:    {final_action} {recommended_contracts} {final_asset} <\n"
        out_str += "=" * 55 + "\n"

        st.code(out_str, language="text")

# --- SEBI COMPLIANCE DISCLAIMER ---
st.markdown("---")
st.caption("⚠️ **Disclaimer:** This tool is for educational and informational purposes only. The creator is **not** a SEBI-registered investment advisor. Options trading and hedging involve significant financial risk. The calculations provided by this tool are mathematical estimates based on historical data and do not guarantee future market performance. Always consult with a qualified financial advisor and conduct your own risk assessment before executing any live trades.")
