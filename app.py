import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime

# --- PAGE CONFIG ---
st.set_page_config(page_title="Beta Hedge Calculator | Part Time IT Investor", layout="wide", page_icon="📈")

# --- HIDE STREAMLIT BRANDING ---
hide_st_style = """
            <style>
            /* Hide top header menu */
            #MainMenu {visibility: hidden;}
            /* Hide default footer */
            footer {visibility: hidden;}
            /* Hide top header completely */
            header {visibility: hidden;}
            /* Hide Streamlit Toolbar (top right) */
            [data-testid="stToolbar"] {visibility: hidden !important;}
            /* Hide Viewer Badge (Hosted with Streamlit) */
            [data-testid="stViewerBadge"] {display: none !important;}
            /* Catch-all for dynamic viewer badge classes */
            [class^="viewerBadge"] {display: none !important;}
            /* Hide any floating Streamlit logos/links */
            a[href^="https://streamlit.io/cloud"] {display: none !important;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# --- SIDEBAR: PARAMETERS ---
st.sidebar.header("Hedging Parameters")
index_symbol = st.sidebar.text_input("Index Symbol (Yahoo Format)", value="^NSEI", help="^NSEI is Nifty 50. ^NSEBANK is Bank Nifty.")
lot_size = st.sidebar.number_input("Index Lot Size", value=50, step=1)
target_delta = st.sidebar.number_input("Target Put Delta", value=0.5, step=0.05, help="0.5 represents an At-The-Money (ATM) Put.")

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
youtube_link = "https://www.youtube.com/channel/UCl1-Z3vCL3zUNjlLlT_Lsxg" # <--- PUT YOUR CHANNEL LINK HERE
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
# --- CORE LOGIC ---
@st.cache_data(ttl=3600)
def fetch_yf_data(ticker, days=365):
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=days)
    try:
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if data.empty:
            return pd.Series(dtype=float)
        return data['Close'].squeeze()
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
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                if 'Instrument' in df.columns and 'Qty.' in df.columns and 'Avg. cost' in df.columns:
                    for index, row in df.iterrows():
                        sym = str(row['Instrument']).strip()
                        try:
                            qty = float(row['Qty.'])
                            avg_price = float(row['Avg. cost'])
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
                else:
                    st.error("Error: Could not find Zerodha's standard columns ('Instrument', 'Qty.', 'Avg. cost').")
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
            
            if stock_closes.empty:
                item['LTP'] = 0.0
                item['P&L'] = 0.0
                item['Beta'] = 1.0 
                continue
            
            ltp = float(stock_closes.iloc[-1])
            qty = item['Qty']
            avg_price = item['Avg Price']
            
            invested = qty * avg_price
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

        beta_weighted_value = total_current_value * portfolio_beta
        exact_contracts = beta_weighted_value / (index_ltp * lot_size * target_delta)
        recommended_contracts = round(exact_contracts)

        st.success("Analysis Complete!")
        
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
            beta = item.get('Beta', 1.0)
            
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
        out_str += f"Option Delta Used:           {target_delta}\n"
        out_str += "-" * 55 + "\n"
        out_str += f"Exact Puts Required:         {exact_contracts:.2f}\n"
        out_str += f"> RECOMMENDED HEDGE:         BUY {recommended_contracts} LOTS <\n"
        out_str += "=" * 55 + "\n"

        st.code(out_str, language="text")
