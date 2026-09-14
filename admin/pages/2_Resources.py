import os

import streamlit as st
from database import supabase
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Resources | Anime World", page_icon="🎬", layout="wide")
st.title("🎬 Anime Resources")
st.caption("Create resources and generate the Telegram deep link. Files remain on Google Drive.")
st.divider()

BOT_USERNAME = os.getenv("BOT_USERNAME", "").strip().lstrip("@")
if not BOT_USERNAME:
    st.warning("BOT_USERNAME is not set. Add it to .env so generated Telegram links use your bot username.")

try:
    channel_rows = supabase.table("telegram_channels").select("id,name").eq("is_active", True).order("name").execute().data or []
except Exception as exc:
    st.error(f"Failed to load channels: {exc}")
    channel_rows = []

st.subheader("➕ Add New Resource")
with st.form("add_resource_form"):
    name = st.text_input("Anime / Resource Name", placeholder="Example: Example Anime — Complete Series")
    drive_url = st.text_input("Google Drive Link", placeholder="https://drive.google.com/...")
    options = {f"{row['name']} (ID {row['id']})": row['id'] for row in channel_rows}
    selected = st.multiselect("Required Channels", list(options), help="Users must be members of every selected channel.")
    active = st.checkbox("Resource is active", True)
    submitted = st.form_submit_button("➕ Create Resource", use_container_width=True)

if submitted:
    name = name.strip()
    drive_url = drive_url.strip()
    if not name:
        st.error("Please enter a resource name.")
    elif not drive_url:
        st.error("Please enter the Google Drive link.")
    elif not selected:
        st.error("Please select at least one required channel.")
    else:
        try:
            duplicate = supabase.table("resources").select("id").eq("name", name).limit(1).execute()
            if duplicate.data:
                st.warning("A resource with this name already exists.")
            else:
                created = supabase.table("resources").insert({
                    "name": name,
                    "drive_url": drive_url,
                    "is_active": active,
                }).execute()
                if not created.data:
                    raise RuntimeError("Supabase did not return the new resource.")
                rid = created.data[0]["id"]
                rows = [{"resource_id": rid, "channel_id": options[label]} for label in selected]
                try:
                    supabase.table("resource_required_channels").insert(rows).execute()
                except Exception:
                    # Roll back the resource when relationship creation fails.
                    supabase.table("resources").delete().eq("id", rid).execute()
                    raise
                st.success("Resource created successfully.")
                if BOT_USERNAME:
                    st.code(f"https://t.me/{BOT_USERNAME}?start=resource_{rid}")
                st.rerun()
        except Exception as exc:
            st.error(f"Failed to create resource: {exc}")

st.divider()
st.subheader("📋 Existing Resources")
try:
    resources = supabase.table("resources").select("*").order("created_at", desc=True).execute().data or []
except Exception as exc:
    st.error(f"Failed to load resources: {exc}")
    resources = []

if not resources:
    st.info("No resources have been created yet.")

for resource in resources:
    rid = resource["id"]
    active = resource.get("is_active", True)
    bot_link = f"https://t.me/{BOT_USERNAME}?start=resource_{rid}" if BOT_USERNAME else None
    with st.container(border=True):
        c1, c2 = st.columns([5, 1])
        c1.markdown(f"### 🎬 {resource.get('name', 'Unnamed Resource')}")
        c2.write("**Active**" if active else "**Inactive**")
        st.write(f"Resource ID: `{rid}`")
        st.write("**Google Drive Link**")
        st.code(resource.get("drive_url") or "Not configured")
        st.write("**Telegram Deep Link**")
        st.code(bot_link or "Set BOT_USERNAME in .env")
        try:
            required = supabase.table("resource_required_channels").select("channel_id, telegram_channels(name)").eq("resource_id", rid).execute().data or []
            names = []
            for row in required:
                channel = row.get("telegram_channels")
                if isinstance(channel, list):
                    channel = channel[0] if channel else None
                if channel:
                    names.append(channel.get("name", "Unnamed Channel"))
            st.write("**Required Channels:** " + (", ".join(names) if names else "None"))
        except Exception as exc:
            st.warning(f"Could not load required channels: {exc}")
        a, b = st.columns(2)
        if a.button("⛔ Disable" if active else "✅ Enable", key=f"toggle_resource_{rid}", use_container_width=True):
            supabase.table("resources").update({"is_active": not active}).eq("id", rid).execute()
            st.rerun()
        if b.button("🗑️ Delete", key=f"delete_resource_{rid}", use_container_width=True):
            try:
                supabase.table("resource_required_channels").delete().eq("resource_id", rid).execute()
            except Exception:
                pass
            supabase.table("resources").delete().eq("id", rid).execute()
            st.rerun()
