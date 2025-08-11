import streamlit as st

st.set_page_config(page_title="Streamlit Blog", page_icon="📝", layout="centered")

st.title("Streamlit Blog")

st.page_link("pages/1_Blog.py", label="Public Blog", icon="📰")
st.page_link("pages/2_Admin.py", label="Admin Panel", icon="🛠️")