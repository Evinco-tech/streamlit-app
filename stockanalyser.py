import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import feedparser
from textblob import TextBlob

st.set_page_config(
    page_title="STOCK ANALYZER",
    page_icon="",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS ---
st.markdown("""
<style>
  .company-card {
        padding: 20px;
        border-radius: 15px;
        background: linear-gradient(135deg, #1e1e2e 0%, #2d2d44 100%);
        border: 1px solid #444;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
        transition: transform 0.2s;
    }
  .company-card:hover {
        transform: translateY(-5px);
        border: 1px solid #00d4ff;
    }
  .big-font { font-size:30px!important; font-weight:700; }
  .green { color: #00ff88; }
  .red { color: #ff4b4b; }
  .sentiment-good { color: #00ff88; font-weight: bold; }
  .sentiment-bad { color: #ff4b4b; font-weight: bold; }
  .sentiment-neutral { color: #ffaa00; font-weight: bold; }
  .stButton>button { width: 100%; }
</style>
""", unsafe_allow_html=True)

NSE_COMPANIES = {
    "Safaricom": {"ticker": "SCOM.NR", "sector": "Telecom", "logo": "", "keyword": "Safaricom"},
    "KCB Group": {"ticker": "KCB.NR", "sector": "Banking", "logo": "", "keyword": "KCB"},
    "Equity Group": {"ticker": "EQTY.NR", "sector": "Banking", "logo": "", "keyword": "Equity"},
    "EABL": {"ticker": "EABL.NR", "sector": "Brewing", "logo": "", "keyword": "EABL"},
    "Co-op Bank": {"ticker": "COOP.NR", "sector": "Banking", "logo": "", "keyword": "Co-operative Bank"},
    "Bamburi Cement": {"ticker": "BAMB.NR", "sector": "Construction", "logo": "", "keyword": "Bamburi"},
    "KenGen": {"ticker": "KEGN.NR", "sector": "Energy", "logo": "", "keyword": "KenGen"},
    "BAT Kenya": {"ticker": "BAT.NR", "sector": "Consumer", "logo": "", "keyword": "BAT Kenya"},
}

@st.cache_data(ttl=60)
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1d", interval="5m")
        info = stock.info
        if hist.empty: return None
        current_price = hist['Close'].iloc[-1]
        prev_close = info.get('previousClose', hist['Close'].iloc[0])
        change = current_price - prev_close
        change_pct = (change / prev_close) * 100
        return {
            "price": current_price, "change": change, "change_pct": change_pct,
            "hist": hist, "volume": hist['Volume'].sum(),
            "day_high": hist['High'].max(), "day_low": hist['Low'].min()
        }
    except: return None

@st.cache_data(ttl=1800) # Cache news for 30 mins
def get_news_sentiment(company_keyword):
    """Pull Google News + analyze sentiment with AI"""
    try:
        # Google News RSS for Kenya
        url = f"https://news.google.com/rss/search?q={company_keyword}+Kenya+NSE&hl=en-KE&gl=KE&ceid=KE:en"
        feed = feedparser.parse(url)
        
        headlines = [entry.title for entry in feed.entries[:5]] # Top 5 headlines
        if not headlines:
            return {"score": 0, "label": "Neutral", "headlines": []}
        
        # Analyze sentiment with TextBlob
        scores = [TextBlob(h).sentiment.polarity for h in headlines]
        avg_score = sum(scores) / len(scores)
        
        if avg_score > 0.1:
            label = "Good "
            css_class = "sentiment-good"
        elif avg_score < -0.1:
            label = "Bad "
            css_class = "sentiment-bad"
        else:
            label = "Neutral "
            css_class = "sentiment-neutral"
            
        return {"score": avg_score, "label": label, "css_class": css_class, "headlines": headlines}
    except:
        return {"score": 0, "label": "Neutral", "css_class": "sentiment-neutral", "headlines": []}

def explain_in_simple_terms(data, company_name, sentiment):
    if not data:
        return "We couldn't get data right now. Market might be closed."
    
    price, change, change_pct = data['price'], data['change_pct']
    
    if change > 0:
        trend = f"going UP 📈 by KES {change:.2f}"
        meaning = "If you owned shares, they're worth more than yesterday."
    elif change < 0:
        trend = f"going DOWN 📉 by KES {abs(change):.2f}"
        meaning = "Shares are cheaper than yesterday."
    else:
        trend = "not moving ↔️"
        meaning = "Price is the same as yesterday."
    
    return f"""
    **In simple terms:** {company_name} stock is {trend} ({change_pct:.2f}%).
    
    **What this means:** {meaning}
    
    **News mood today:** {sentiment['label']} - Based on recent headlines.
    
    **Today's range:** KES {data['day_low']:.2f} - KES {data['day_high']:.2f} | **Volume:** {data['volume']:,} shares
    """

# --- Main App ---
st.markdown("<h1 style='text-align: center;'>STOCK ANALYZER</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #888;'>Real-time NSE insights + AI news sentiment for everyone</p>", unsafe_allow_html=True)

if 'selected_company' not in st.session_state:
    st.session_state.selected_company = None

# --- Dashboard View ---
if st.session_state.selected_company is None:
    st.subheader("Top NSE Companies Today")
    cols = st.columns(4)
    
    for idx, (name, details) in enumerate(NSE_COMPANIES.items()):
        data = get_stock_data(details['ticker'])
        sentiment = get_news_sentiment(details['keyword'])
        
        with cols[idx % 4]:
            st.markdown('<div class="company-card">', unsafe_allow_html=True)
            if data:
                color = "green" if data['change'] >= 0 else "red"
                arrow = "▲" if data['change'] >= 0 else "▼"
                st.markdown(f"### {details['logo']} {name}")
                st.markdown(f"<p class='big-font'>KES {data['price']:.2f}</p>", unsafe_allow_html=True)
                st.markdown(f"<p class='{color}'>{arrow} {data['change']:.2f} ({data['change_pct']:.2f}%)</p>", unsafe_allow_html=True)
                st.markdown(f"News Mood: <span class='{sentiment['css_class']}'>{sentiment['label']}</span>", unsafe_allow_html=True)
            else:
                st.markdown(f"### {details['logo']} {name}")
                st.markdown("<p class='big-font'>No Data</p>", unsafe_allow_html=True)
            
            if st.button(f"Analyze {name}", key=name):
                st.session_state.selected_company = name
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            st.write("")

# --- Detailed Analysis View ---
else:
    company = st.session_state.selected_company
    details = NSE_COMPANIES[company]
    data = get_stock_data(details['ticker'])
    sentiment = get_news_sentiment(details['keyword'])
    
    if st.button("← Back to Dashboard"):
        st.session_state.selected_company = None
        st.rerun()
    
    st.header(f"{details['logo']} {company} - {details['sector']}")
    
    if data:
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Current Price", f"KES {data['price']:.2f}", f"{data['change']:.2f} ({data['change_pct']:.2f}%)")
        col2.metric("Day High", f"KES {data['day_high']:.2f}")
        col3.metric("Day Low", f"KES {data['day_low']:.2f}")
        col4.metric("News Sentiment", sentiment['label'])
        
        # Chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data['hist'].index, y=data['hist']['Close'], mode='lines', line=dict(color='#00d4ff', width=3)))
        fig.update_layout(title=f"{company} Price Today", template="plotly_dark", height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Simple Explanation + News
        col1, col2 = st.columns([1,1])
        with col1:
            st.subheader(" Explained Simply")
            st.info(explain_in_simple_terms(data, company, sentiment))
        with col2:
            st.subheader(" Latest Headlines")
            if sentiment['headlines']:
                for h in sentiment['headlines']:
                    st.write(f"• {h}")
            else:
                st.write("No recent news found.")
    else:
        st.error("Could not fetch data. NSE trading hours: 9:00 AM - 3:00 PM EAT, Mon-Fri")

st.caption(f"Last updated: {datetime.now().strftime('%H:%M:%S')} EAT | News from Google | Not financial advice")