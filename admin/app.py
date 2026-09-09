import streamlit as st

from database import supabase


st.set_page_config(
    page_title="Anime World Admin",
    page_icon="🎬",
    layout="wide"
)


st.title("🎬 Anime World Admin")

st.divider()


resources = (
    supabase
    .table("resources")
    .select("id")
    .execute()
)

channels = (
    supabase
    .table("telegram_channels")
    .select("id")
    .execute()
)

users = (
    supabase
    .table("users")
    .select("id")
    .execute()
)


col1, col2, col3 = st.columns(3)


with col1:

    st.metric(
        "Resources",
        len(resources.data)
    )


with col2:

    st.metric(
        "Channels",
        len(channels.data)
    )


with col3:

    st.metric(
        "Users",
        len(users.data)
    )