"""Página Banco Internacional."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from pathlib import Path
from PIL import Image
import streamlit as st
from utils import render_dashboard

_icon_path = Path(__file__).parent.parent / "banco_internacional.png"
_icon = Image.open(_icon_path) if _icon_path.exists() else "🏦"

st.set_page_config(page_title="Banco Internacional", page_icon=_icon, layout="wide")
render_dashboard(bank_filter="Banco Internacional")
