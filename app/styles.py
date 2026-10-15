"""Small, responsive presentation layer for the insurance laboratory."""
import streamlit as st


def apply_styles():
    st.markdown("""<style>
    .stApp { background:#f4f7fa; color:#142d43; }
    [data-testid="stSidebar"] { background:#102b40; }
    [data-testid="stSidebar"] * { color:#f0f6fa; }
    [data-testid="stSidebar"] [data-baseweb="radio"] { padding:5px 0; }
    .block-container { max-width:1320px; padding-top:2.5rem; padding-bottom:3rem; }
    h1,h2,h3 { color:#102b40; letter-spacing:-.025em; }
    h1 { font-size:2.65rem !important; }
    [data-testid="stMetric"] { background:white; border:1px solid #dfe8ee;
      border-radius:12px; padding:18px 20px; min-height:110px; }
    [data-testid="stMetricLabel"] { color:#486174; }
    [data-testid="stMetricValue"] { color:#126f73; font-size:1.7rem; }
    .eyebrow { color:#147b7d; letter-spacing:.13em; font-size:.76rem; font-weight:700; }
    .lead { color:#486174; font-size:1.12rem; max-width:850px; line-height:1.65; }
    .evidence { background:#e7f2f1; border-left:4px solid #147b7d;
      border-radius:0 8px 8px 0; padding:16px 20px; margin:16px 0; }
    .stPlotlyChart { background:white; border:1px solid #e1e9ef; border-radius:12px; }
    [data-testid="stDataFrame"] { border-radius:8px; }
    a { color:#08787c; }
    [data-testid="stSidebar"] a, [data-testid="stSidebar"] a span { color:#a7dfdc !important; }
    a:focus-visible, button:focus-visible { outline:3px solid #36a5a3; outline-offset:3px; }
    @media(max-width:640px) { .block-container { padding:1.25rem 1rem; }
      h1 {font-size:2rem !important;} [data-testid="stMetric"]{padding:12px;min-height:95px;}
      [data-testid="stMetricValue"] {font-size:1.4rem;} }
    </style>""", unsafe_allow_html=True)
