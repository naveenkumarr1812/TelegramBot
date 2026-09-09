import streamlit as st

from database import supabase


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Channels | Anime World",
    page_icon="📢",
    layout="wide",
)


# ============================================================
# PAGE TITLE
# ============================================================

st.title("📢 Telegram Channels")

st.write(
    "Manage the Telegram channels that users "
    "must join before accessing resources."
)

st.divider()


# ============================================================
# ADD CHANNEL
# ============================================================

st.subheader("➕ Add New Channel")


with st.form("add_channel_form"):

    col1, col2 = st.columns(2)

    with col1:

        name = st.text_input(
            "Channel Name",
            placeholder="Example: Test Channel 1",
        )

        chat_id = st.text_input(
            "Telegram Chat ID",
            placeholder="Example: -1001234567890",
            help=(
                "The Telegram channel ID. "
                "Usually starts with -100."
            ),
        )

    with col2:

        username = st.text_input(
            "Channel Username",
            placeholder="Example: @testchannel",
            help=(
                "Enter the public Telegram username "
                "if the channel has one."
            ),
        )

        invite_link = st.text_input(
            "Invite Link",
            placeholder="https://t.me/testchannel",
            help=(
                "The link users will click to join "
                "the channel."
            ),
        )

    submitted = st.form_submit_button(
        "➕ Add Channel",
        use_container_width=True,
    )


# ============================================================
# INSERT CHANNEL
# ============================================================

if submitted:

    # --------------------------------------------------------
    # Validate channel name
    # --------------------------------------------------------

    if not name.strip():

        st.error(
            "❌ Please enter a channel name."
        )

    # --------------------------------------------------------
    # Validate Chat ID
    # --------------------------------------------------------

    elif not chat_id.strip():

        st.error(
            "❌ Please enter the Telegram Chat ID."
        )

    else:

        try:

            # Convert Chat ID to integer
            telegram_chat_id = int(
                chat_id.strip()
            )

        except ValueError:

            st.error(
                "❌ Chat ID must be a number.\n\n"
                "Example: -1001234567890"
            )

        else:

            try:

                # ------------------------------------------------
                # Check whether channel already exists
                # ------------------------------------------------

                existing = (
                    supabase
                    .table("telegram_channels")
                    .select("id")
                    .eq(
                        "chat_id",
                        telegram_chat_id,
                    )
                    .execute()
                )

                if existing.data:

                    st.warning(
                        "⚠️ This Telegram channel "
                        "already exists."
                    )

                else:

                    # ------------------------------------------------
                    # Insert channel
                    # ------------------------------------------------

                    result = (
                        supabase
                        .table("telegram_channels")
                        .insert(
                            {
                                "name": name.strip(),
                                "chat_id": telegram_chat_id,
                                "username": (
                                    username.strip()
                                    if username.strip()
                                    else None
                                ),
                                "invite_link": (
                                    invite_link.strip()
                                    if invite_link.strip()
                                    else None
                                ),
                                "is_active": True,
                            }
                        )
                        .execute()
                    )

                    if result.data:

                        st.success(
                            "✅ Channel added successfully!"
                        )

                        st.rerun()

                    else:

                        st.error(
                            "❌ Failed to add channel."
                        )

            except Exception as error:

                st.error(
                    f"❌ Database error: {error}"
                )


st.divider()


# ============================================================
# EXISTING CHANNELS
# ============================================================

st.subheader("📋 Existing Channels")


try:

    response = (
        supabase
        .table("telegram_channels")
        .select("*")
        .order(
            "created_at",
            desc=True,
        )
        .execute()
    )

    channels = response.data

except Exception as error:

    st.error(
        f"❌ Failed to load channels: {error}"
    )

    channels = []


# ============================================================
# NO CHANNELS
# ============================================================

if not channels:

    st.info(
        "No Telegram channels have been added yet."
    )


# ============================================================
# DISPLAY CHANNELS
# ============================================================

else:

    for channel in channels:

        channel_id = channel["id"]

        channel_name = channel.get(
            "name",
            "Unnamed Channel",
        )

        is_active = channel.get(
            "is_active",
            True,
        )

        with st.container(border=True):

            # ------------------------------------------------
            # Header
            # ------------------------------------------------

            col1, col2, col3 = st.columns(
                [4, 2, 1]
            )

            with col1:

                st.markdown(
                    f"### 📢 {channel_name}"
                )

            with col2:

                if is_active:

                    st.success(
                        "Active"
                    )

                else:

                    st.warning(
                        "Inactive"
                    )

            with col3:

                st.write(
                    f"ID: `{channel_id}`"
                )

            # ------------------------------------------------
            # Channel information
            # ------------------------------------------------

            info_col1, info_col2 = st.columns(2)

            with info_col1:

                st.write(
                    "**Telegram Chat ID:**"
                )

                st.code(
                    str(
                        channel["chat_id"]
                    )
                )

                st.write(
                    "**Username:**"
                )

                username_value = (
                    channel.get("username")
                    or "Not provided"
                )

                st.code(
                    username_value
                )

            with info_col2:

                st.write(
                    "**Invite Link:**"
                )

                invite_link_value = (
                    channel.get(
                        "invite_link"
                    )
                    or "Not provided"
                )

                st.code(
                    invite_link_value
                )

                st.write(
                    "**Created:**"
                )

                st.write(
                    channel.get(
                        "created_at",
                        "Unknown",
                    )
                )

            # ------------------------------------------------
            # Actions
            # ------------------------------------------------

            st.write("")

            action_col1, action_col2 = st.columns(2)

            with action_col1:

                toggle_text = (
                    "⛔ Disable Channel"
                    if is_active
                    else "✅ Enable Channel"
                )

                if st.button(
                    toggle_text,
                    key=f"toggle_{channel_id}",
                    use_container_width=True,
                ):

                    try:

                        (
                            supabase
                            .table(
                                "telegram_channels"
                            )
                            .update(
                                {
                                    "is_active": (
                                        not is_active
                                    )
                                }
                            )
                            .eq(
                                "id",
                                channel_id,
                            )
                            .execute()
                        )

                        st.success(
                            "Channel status updated."
                        )

                        st.rerun()

                    except Exception as error:

                        st.error(
                            f"Failed to update channel: "
                            f"{error}"
                        )

            with action_col2:

                if st.button(
                    "🗑️ Delete Channel",
                    key=f"delete_{channel_id}",
                    use_container_width=True,
                ):

                    try:

                        (
                            supabase
                            .table(
                                "telegram_channels"
                            )
                            .delete()
                            .eq(
                                "id",
                                channel_id,
                            )
                            .execute()
                        )

                        st.success(
                            "Channel deleted successfully."
                        )

                        st.rerun()

                    except Exception as error:

                        st.error(
                            f"Failed to delete channel: "
                            f"{error}"
                        )