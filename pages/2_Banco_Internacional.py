"""Página Banco Internacional."""
import streamlit as st
from utils import render_dashboard

st.set_page_config(page_title="Banco Internacional", page_icon="https://relif.com/favicon.png", layout="wide")
render_dashboard(bank_filter="Banco Internacional")
