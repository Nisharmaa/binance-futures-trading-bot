"""
app.py — Streamlit UI for Binance Futures Testnet Trading Bot
-------------------------------------------------------------
Run with:
    pip install streamlit requests
    streamlit run app.py
"""
from dotenv import load_dotenv
import os
import json
import time
import streamlit as st

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")

# Import our backend order functions
from orders import (
    validate_order,
    place_order_mock,
    place_order_live,
    get_account_balance_mock,
)
# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG  (must be the very first Streamlit call)
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Binance Futures Testnet Bot",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL CSS — dark trading terminal aesthetic
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(
    """
    <style>
    /* ── Import fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600;700&family=Syne:wght@400;600;800&display=swap');

    /* ── Root palette ── */
    :root {
        --bg-base:      #0a0c10;
        --bg-card:      #10141c;
        --bg-input:     #171c28;
        --border:       #1e2535;
        --border-focus: #f0b90b;
        --text-primary: #e8eaf0;
        --text-muted:   #5a6480;
        --text-label:   #8892a4;
        --accent:       #f0b90b;   /* Binance yellow */
        --accent-dim:   #c49709;
        --green:        #0ecb81;
        --red:          #f6465d;
        --blue:         #1890ff;
        --radius:       8px;
    }

    /* ── Global resets ── */
    html, body, [data-testid="stAppViewContainer"],
    [data-testid="stApp"] {
        background-color: var(--bg-base) !important;
        color: var(--text-primary) !important;
        font-family: 'Syne', sans-serif;
    }

    /* Hide Streamlit chrome */
    #MainMenu, footer, header { visibility: hidden; }
    [data-testid="stToolbar"] { display: none; }

    /* ── Typography ── */
    h1, h2, h3, h4 { font-family: 'Syne', sans-serif; letter-spacing: -0.02em; }

    /* ── Input fields ── */
    [data-testid="stTextInput"] input,
    [data-testid="stNumberInput"] input,
    [data-testid="stSelectbox"] div[data-baseweb="select"] {
        background-color: var(--bg-input) !important;
        border: 1px solid var(--border) !important;
        border-radius: var(--radius) !important;
        color: var(--text-primary) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.9rem !important;
        transition: border-color 0.15s ease;
    }
    [data-testid="stTextInput"] input:focus,
    [data-testid="stNumberInput"] input:focus {
        border-color: var(--accent) !important;
        box-shadow: 0 0 0 2px rgba(240,185,11,0.15) !important;
        outline: none !important;
    }

    /* ── Labels ── */
    label, [data-testid="stWidgetLabel"] p {
        color: var(--text-label) !important;
        font-size: 0.75rem !important;
        font-family: 'JetBrains Mono', monospace !important;
        letter-spacing: 0.08em !important;
        text-transform: uppercase !important;
        font-weight: 600 !important;
    }

    /* ── Primary button (Place Order) ── */
    [data-testid="stButton"] > button[kind="primary"],
    [data-testid="stButton"] > button {
        background: linear-gradient(135deg, #f0b90b 0%, #c49709 100%) !important;
        color: #0a0c10 !important;
        border: none !important;
        border-radius: var(--radius) !important;
        font-family: 'Syne', sans-serif !important;
        font-weight: 800 !important;
        font-size: 1rem !important;
        letter-spacing: 0.04em !important;
        padding: 0.65rem 2rem !important;
        width: 100%;
        cursor: pointer;
        transition: opacity 0.15s ease, transform 0.1s ease !important;
    }
    [data-testid="stButton"] > button:hover {
        opacity: 0.88 !important;
        transform: translateY(-1px) !important;
    }
    [data-testid="stButton"] > button:active {
        transform: translateY(0) !important;
    }

    /* ── Cards / containers ── */
    .card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 12px;
        padding: 1.5rem 1.75rem;
        margin-bottom: 1rem;
    }
    .card-accent {
        border-left: 3px solid var(--accent);
    }
    .card-green  { border-left: 3px solid var(--green); }
    .card-red    { border-left: 3px solid var(--red);   }

    /* ── Metric chips ── */
    .metric-row  { display: flex; gap: 1rem; margin-bottom: 1.25rem; flex-wrap: wrap; }
    .metric-chip {
        background: var(--bg-input);
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 0.5rem 1rem;
        flex: 1; min-width: 120px;
    }
    .metric-chip .label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    .metric-chip .value {
        font-family: 'JetBrains Mono', monospace;
        font-size: 1.05rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-top: 2px;
    }
    .metric-chip .value.green { color: var(--green); }
    .metric-chip .value.yellow { color: var(--accent); }

    /* ── Status badge ── */
    .badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 20px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        text-transform: uppercase;
    }
    .badge-green  { background: rgba(14,203,129,.15); color: var(--green); }
    .badge-yellow { background: rgba(240,185,11,.15); color: var(--accent); }
    .badge-red    { background: rgba(246,70,93,.15);  color: var(--red);   }
    .badge-blue   { background: rgba(24,144,255,.15); color: var(--blue);  }

    /* ── Section headers ── */
    .section-title {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        color: var(--text-muted);
        text-transform: uppercase;
        letter-spacing: 0.15em;
        margin-bottom: 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .section-title::after {
        content: '';
        flex: 1;
        height: 1px;
        background: var(--border);
    }

    /* ── JSON response block ── */
    .json-block {
        background: #0d1117;
        border: 1px solid var(--border);
        border-radius: var(--radius);
        padding: 1rem 1.25rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.78rem;
        color: #7dd3a8;
        overflow-x: auto;
        white-space: pre;
        line-height: 1.6;
    }

    /* ── Divider ── */
    hr { border-color: var(--border) !important; margin: 1.5rem 0 !important; }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: var(--bg-card) !important;
        border-right: 1px solid var(--border) !important;
    }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-base); }
    ::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }

    /* ── Alert overrides ── */
    [data-testid="stAlert"] {
        border-radius: var(--radius) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.82rem !important;
    }

    /* ── Spinner ── */
    [data-testid="stSpinner"] { color: var(--accent) !important; }

    /* ── Streamlit selectbox dropdown ── */
    [data-baseweb="popover"] { background: var(--bg-input) !important; }
    li[role="option"] { color: var(--text-primary) !important; background: var(--bg-input) !important; }
    li[role="option"]:hover { background: var(--border) !important; }

    /* remove default padding from main block */
    .block-container { padding-top: 2rem !important; padding-bottom: 2rem !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════════════════════════════════
# SESSION STATE — persists values across reruns
# ═══════════════════════════════════════════════════════════════════════════════
if "order_history" not in st.session_state:
    st.session_state.order_history = []   # list of past order results
if "last_response" not in st.session_state:
    st.session_state.last_response = None
if "last_error" not in st.session_state:
    st.session_state.last_error = None
if "order_count" not in st.session_state:
    st.session_state.order_count = 0

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(
    """
    <div style="display:flex; align-items:center; gap:1rem; margin-bottom:0.25rem;">
        <div style="font-size:2rem;">⚡</div>
        <div>
            <div style="font-family:'Syne',sans-serif; font-size:1.55rem;
                        font-weight:800; color:#e8eaf0; letter-spacing:-0.03em;
                        line-height:1.1;">
                Binance Futures Testnet
            </div>
            <div style="font-family:'Syne',sans-serif; font-size:1.55rem;
                        font-weight:800; color:#f0b90b; letter-spacing:-0.03em;
                        line-height:1.1;">
                Trading Bot
            </div>
        </div>
        <div style="margin-left:auto;">
            <span class="badge badge-yellow">TESTNET</span>
        </div>
    </div>
    <p style="color:#5a6480; font-family:'JetBrains Mono',monospace;
              font-size:0.78rem; margin-bottom:1.5rem;">
        Live Binance Futures Testnet connected
    </p>
    """,
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════════════════════════════════
# ACCOUNT BALANCE BAR
# ═══════════════════════════════════════════════════════════════════════════════
# ACCOUNT BALANCE BAR
# ═══════════════════════════════════════════════════════════════════════════════

balances = get_account_balance_mock()

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("USDT Balance", balances[0]["balance"])

with col2:
    st.metric("USDT Available", balances[0]["availableBalance"])

with col3:
    st.metric("BTC Balance", balances[1]["balance"])

with col4:
    st.metric("BTC Available", balances[1]["availableBalance"])

with col5:
    st.metric("Orders Placed", st.session_state.order_count)

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN LAYOUT — two columns: Order Form | Results
# ═══════════════════════════════════════════════════════════════════════════════
col_form, col_results = st.columns([1, 1.15], gap="large")

# ─────────────────────────────────────────────
# LEFT COLUMN — Order Form
# ─────────────────────────────────────────────
with col_form:
    st.markdown('<div class="section-title">New Order</div>', unsafe_allow_html=True)

    with st.container():
       # st.markdown('<div class="card card-accent">', unsafe_allow_html=True)

        # Symbol input
        symbol = st.text_input(
            "Symbol",
            value="BTCUSDT",
            placeholder="e.g. BTCUSDT, ETHUSDT",
            help="Futures trading pair (must exist on Binance Futures)",
        ).strip().upper()

        # Side & Order Type — side by side
        c1, c2 = st.columns(2)
        with c1:
            side = st.selectbox(
                "Side",
                options=["BUY", "SELL"],
                help="BUY to go long, SELL to go short",
            )
        with c2:
            order_type = st.selectbox(
                "Order Type",
                options=["MARKET", "LIMIT"],
                help="MARKET executes immediately; LIMIT waits for your price",
            )

        # Quantity
        quantity = st.number_input(
            "Quantity",
            min_value=0.0,
            value=0.001,
            step=0.001,
            format="%.4f",
            help="Amount of base asset to trade (e.g. BTC for BTCUSDT)",
        )

        # Price — only visible for LIMIT orders
        price: float | None = None
        if order_type == "LIMIT":
            price = st.number_input(
                "Limit Price (USDT)",
                min_value=0.0,
                value=40000.0,
                step=10.0,
                format="%.2f",
                help="Your target price. Order fills when market reaches this level.",
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Place Order button
        place_order_btn = st.button("⚡ Place Order", use_container_width=True)

        #st.markdown("</div>", unsafe_allow_html=True)

    # Order Summary (updates live as user types)
    st.markdown('<div class="section-title">Order Summary</div>', unsafe_allow_html=True)
    price_display = f"${price:,.2f}" if order_type == "LIMIT" and price else "Market Price"
    side_color    = "green" if side == "BUY" else "red"
    side_badge    = f'<span class="badge badge-{side_color}">{side}</span>'
    type_badge    = '<span class="badge badge-blue">LIMIT</span>' if order_type == "LIMIT" else '<span class="badge badge-yellow">MARKET</span>'

    st.markdown(
        f"""
        <div class="card">
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.75rem;">
                <div>
                    <div style="font-family:'JetBrains Mono',monospace; font-size:0.65rem;
                                color:#5a6480; text-transform:uppercase; letter-spacing:.1em;">Symbol</div>
                    <div style="font-family:'JetBrains Mono',monospace; font-size:1rem;
                                font-weight:700; color:#e8eaf0; margin-top:3px;">{symbol or "—"}</div>
                </div>
                <div>
                    <div style="font-family:'JetBrains Mono',monospace; font-size:0.65rem;
                                color:#5a6480; text-transform:uppercase; letter-spacing:.1em;">Side</div>
                    <div style="margin-top:5px;">{side_badge}</div>
                </div>
                <div>
                    <div style="font-family:'JetBrains Mono',monospace; font-size:0.65rem;
                                color:#5a6480; text-transform:uppercase; letter-spacing:.1em;">Type</div>
                    <div style="margin-top:5px;">{type_badge}</div>
                </div>
                <div>
                    <div style="font-family:'JetBrains Mono',monospace; font-size:0.65rem;
                                color:#5a6480; text-transform:uppercase; letter-spacing:.1em;">Quantity</div>
                    <div style="font-family:'JetBrains Mono',monospace; font-size:1rem;
                                font-weight:700; color:#e8eaf0; margin-top:3px;">{quantity:.4f}</div>
                </div>
                <div>
                    <div style="font-family:'JetBrains Mono',monospace; font-size:0.65rem;
                                color:#5a6480; text-transform:uppercase; letter-spacing:.1em;">Price</div>
                    <div style="font-family:'JetBrains Mono',monospace; font-size:1rem;
                                font-weight:700; color:#f0b90b; margin-top:3px;">{price_display}</div>
                </div>
                <div>
                    <div style="font-family:'JetBrains Mono',monospace; font-size:0.65rem;
                                color:#5a6480; text-transform:uppercase; letter-spacing:.1em;">Est. Value</div>
                    <div style="font-family:'JetBrains Mono',monospace; font-size:1rem;
                                font-weight:700; color:#e8eaf0; margin-top:3px;">
                        {"${:,.2f}".format(quantity * price) if order_type == "LIMIT" and price else "—"}
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────
# RIGHT COLUMN — Response & History
# ─────────────────────────────────────────────
with col_results:
    st.markdown('<div class="section-title">Order Response</div>', unsafe_allow_html=True)

    # ── Handle button click ──────────────────────────────────────────────────
    if place_order_btn:
        # Reset previous results
        st.session_state.last_response = None
        st.session_state.last_error    = None

        # 1. Validate inputs
        is_valid, validation_msg = validate_order(symbol, side, order_type, quantity, price)

        if not is_valid:
            # Show validation error immediately
            st.session_state.last_error = f"Validation failed: {validation_msg}"
        else:
            # 2. Place the mock order with a short spinner
            with st.spinner("Placing order on Testnet…"):
                time.sleep(0.6)   # simulate network latency
                try:
                    response = place_order_live(
    API_KEY,
    API_SECRET,
    symbol,
    side,
    order_type,
    quantity,
    price
)
                    st.session_state.last_response = response
                    st.session_state.order_count  += 1
                    # Append to history (keep last 10)
                    st.session_state.order_history.insert(0, response)
                    st.session_state.order_history = st.session_state.order_history[:10]
                except Exception as exc:
                    st.session_state.last_error = str(exc)

    # ── Display last result ──────────────────────────────────────────────────
    if st.session_state.last_error:
        err = st.session_state.last_error
        st.markdown(
            f"""
            <div class="card card-red">
                <div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:0.5rem;">
                    <span style="font-size:1.1rem;">❌</span>
                    <span style="font-family:'Syne',sans-serif; font-weight:700;
                                 color:#f6465d;">Order Failed</span>
                </div>
                <div style="font-family:'JetBrains Mono',monospace; font-size:0.8rem;
                             color:#e8eaf0;">{err}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    elif st.session_state.last_response:
        r = st.session_state.last_response
        status      = r.get("status", "UNKNOWN")
        order_id    = r.get("orderId", "—")
        avg_price   = r.get("avgPrice", "0")
        exec_qty    = r.get("executedQty", "0")
        status_badge = "green" if status == "FILLED" else "yellow"

        st.markdown(
            f"""
            <div class="card card-green">
                <div style="display:flex; align-items:center; gap:0.6rem; margin-bottom:1rem;">
                    <span style="font-size:1.1rem;">✅</span>
                    <span style="font-family:'Syne',sans-serif; font-weight:700;
                                 color:#0ecb81;">Order Submitted Successfully</span>
                    <span class="badge badge-{status_badge}" style="margin-left:auto;">{status}</span>
                </div>
                <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:0.75rem; margin-bottom:1rem;">
                    <div>
                        <div style="font-family:'JetBrains Mono',monospace; font-size:0.6rem;
                                    color:#5a6480; text-transform:uppercase; letter-spacing:.1em;">Order ID</div>
                        <div style="font-family:'JetBrains Mono',monospace; font-size:0.9rem;
                                    font-weight:700; color:#e8eaf0; margin-top:2px;">#{order_id}</div>
                    </div>
                    <div>
                        <div style="font-family:'JetBrains Mono',monospace; font-size:0.6rem;
                                    color:#5a6480; text-transform:uppercase; letter-spacing:.1em;">Avg Fill Price</div>
                        <div style="font-family:'JetBrains Mono',monospace; font-size:0.9rem;
                                    font-weight:700; color:#f0b90b; margin-top:2px;">${float(avg_price):,.2f}</div>
                    </div>
                    <div>
                        <div style="font-family:'JetBrains Mono',monospace; font-size:0.6rem;
                                    color:#5a6480; text-transform:uppercase; letter-spacing:.1em;">Executed Qty</div>
                        <div style="font-family:'JetBrains Mono',monospace; font-size:0.9rem;
                                    font-weight:700; color:#e8eaf0; margin-top:2px;">{exec_qty}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Raw JSON response (collapsible)
        with st.expander("📄 Raw API Response (JSON)", expanded=False):
            st.markdown(
                f'<div class="json-block">{json.dumps(r, indent=2)}</div>',
                unsafe_allow_html=True,
            )

    else:
        # Placeholder when no order has been placed yet
        st.markdown(
            """
            <div class="card" style="text-align:center; padding:2.5rem 1.5rem;">
                <div style="font-size:2.5rem; margin-bottom:0.75rem; opacity:0.3;">📋</div>
                <div style="font-family:'JetBrains Mono',monospace; font-size:0.8rem;
                             color:#5a6480;">
                    Fill in the form and click<br>
                    <strong style="color:#f0b90b;">⚡ Place Order</strong> to see results here
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── Order History ────────────────────────────────────────────────────────
    if st.session_state.order_history:
        st.markdown('<div class="section-title" style="margin-top:1rem;">Order History</div>', unsafe_allow_html=True)

        for i, hist in enumerate(st.session_state.order_history):
            h_status  = hist.get("status", "UNKNOWN")
            h_symbol  = hist.get("symbol", "—")
            h_side    = hist.get("side", "—")
            h_type    = hist.get("type", "—")
            h_qty     = hist.get("origQty", "0")
            h_price   = hist.get("avgPrice", "0")
            h_id      = hist.get("orderId", "—")
            h_side_c  = "green" if h_side == "BUY" else "red"
            h_status_c = "green" if h_status == "FILLED" else "yellow"

            st.markdown(
                f"""
                <div class="card" style="padding:0.85rem 1rem; margin-bottom:0.5rem;">
                    <div style="display:flex; align-items:center; gap:0.5rem; flex-wrap:wrap;">
                        <span style="font-family:'JetBrains Mono',monospace; font-size:0.78rem;
                                     color:#e8eaf0; font-weight:700;">{h_symbol}</span>
                        <span class="badge badge-{h_side_c}">{h_side}</span>
                        <span class="badge badge-blue">{h_type}</span>
                        <span class="badge badge-{h_status_c}">{h_status}</span>
                        <span style="margin-left:auto; font-family:'JetBrains Mono',monospace;
                                     font-size:0.72rem; color:#5a6480;">#{h_id}</span>
                    </div>
                    <div style="display:flex; gap:1.5rem; margin-top:0.4rem;">
                        <span style="font-family:'JetBrains Mono',monospace; font-size:0.72rem; color:#8892a4;">
                            Qty: <strong style="color:#e8eaf0;">{h_qty}</strong>
                        </span>
                        <span style="font-family:'JetBrains Mono',monospace; font-size:0.72rem; color:#8892a4;">
                            Fill: <strong style="color:#f0b90b;">${float(h_price):,.2f}</strong>
                        </span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if st.button("Clear History", use_container_width=False):
            st.session_state.order_history = []
            st.session_state.order_count   = 0
            st.rerun()

# ═══════════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("<br>", unsafe_allow_html=True)
st.markdown(
    """
    <div style="border-top:1px solid #1e2535; padding-top:1rem;
                display:flex; align-items:center; justify-content:space-between;
                flex-wrap:wrap; gap:0.5rem;">
        <span style="font-family:'JetBrains Mono',monospace; font-size:0.7rem; color:#5a6480;">
            ⚡ Binance Futures Testnet Bot &nbsp;·&nbsp; Internship Project
        </span>
        <span style="font-family:'JetBrains Mono',monospace; font-size:0.7rem; color:#5a6480;">
            <span class="badge badge-yellow">TESTNET</span>&nbsp;
            No real funds · Safe to experiment
        </span>
    </div>
    """,
    unsafe_allow_html=True,
)
