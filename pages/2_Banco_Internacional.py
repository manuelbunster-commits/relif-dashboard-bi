"""Página Banco Internacional."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import streamlit as st
from utils import render_dashboard

st.set_page_config(page_title="Banco Internacional", page_icon="https://relif.com/favicon.png", layout="wide")
render_dashboard(bank_filter="Banco Internacional")
