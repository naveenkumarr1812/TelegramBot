import streamlit as st

from database import supabase


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Resources | Anime World",
    page_icon="🎬",
    layout="wide",
)


# ============================================================
# PAGE TITLE
# ============================================================

st.title("🎬 Anime Resources")

st.write(
    "Create and manage anime download resources. "
    "The actual anime files are stored on Google Drive."
)

st.divider()


# ============================================================
# BOT USERNAME
# ============================================================

BOT_USERNAME = "AnimeWorldResourceBot"


# ============================================================
# LOAD CHANNELS
# ============================================================

try:

    channels_response = (
        supabase
        .table("telegram_channels")
        .select("*")
        .eq("is_active", True)
        .order("name")
        .execute()
    )

    channels = channels_response.data or []

except Exception as error:

    st.error(
        f"❌ Failed to load channels: {error}"
    )

    channels = []


# ============================================================
# ADD RESOURCE
# ============================================================

st.subheader("➕ Add New Resource")


if not channels:

    st.warning(
        "⚠️ No active Telegram channels found.\n\n"
        "Please add at least one channel from "
        "the Channels page before creating a resource."
    )

else:

    # --------------------------------------------------------
    # Create channel lookup
    # --------------------------------------------------------

    channel_options = {
        channel["name"]: channel["id"]
        for channel in channels
    }

    with st.form("add_resource_form"):

        # ----------------------------------------------------
        # Resource name
        # ----------------------------------------------------

        resource_name = st.text_input(
            "Anime / Resource Name",
            placeholder="Example: Death Note - Complete Series",
        )

        # ----------------------------------------------------
        # Google Drive URL
        # ----------------------------------------------------

        drive_url = st.text_input(
            "Google Drive Download Link",
            placeholder="https://drive.google.com/...",
            help=(
                "Paste the Google Drive link where "
                "the anime files are stored."
            ),
        )

        # ----------------------------------------------------
        # Required channels
        # ----------------------------------------------------

        st.write(
            "**Required Channels**"
        )

        selected_channel_names = st.multiselect(
            "Select channels users must join",
            options=list(channel_options.keys()),
            help=(
                "Users must join all selected channels "
                "before they receive the Google Drive link."
            ),
        )

        # ----------------------------------------------------
        # Active status
        # ----------------------------------------------------

        is_active = st.checkbox(
            "Resource is active",
            value=True,
        )

        # ----------------------------------------------------
        # Submit
        # ----------------------------------------------------

        submitted = st.form_submit_button(
            "➕ Create Resource",
            use_container_width=True,
        )


    # ========================================================
    # CREATE RESOURCE
    # ========================================================

    if submitted:

        # ----------------------------------------------------
        # Validate resource name
        # ----------------------------------------------------

        if not resource_name.strip():

            st.error(
                "❌ Please enter an anime/resource name."
            )

        # ----------------------------------------------------
        # Validate Google Drive URL
        # ----------------------------------------------------

        elif not drive_url.strip():

            st.error(
                "❌ Please enter the Google Drive link."
            )

        # ----------------------------------------------------
        # Validate channels
        # ----------------------------------------------------

        elif not selected_channel_names:

            st.error(
                "❌ Please select at least one required channel."
            )

        else:

            try:

                # ------------------------------------------------
                # Check duplicate resource
                # ------------------------------------------------

                existing = (
                    supabase
                    .table("resources")
                    .select("id")
                    .eq(
                        "name",
                        resource_name.strip(),
                    )
                    .execute()
                )

                if existing.data:

                    st.warning(
                        "⚠️ A resource with this name "
                        "already exists."
                    )

                else:

                    # ------------------------------------------------
                    # Insert resource
                    # ------------------------------------------------

                    resource_result = (
                        supabase
                        .table("resources")
                        .insert(
                            {
                                "name": resource_name.strip(),
                                "drive_url": drive_url.strip(),
                                "is_active": is_active,
                            }
                        )
                        .execute()
                    )

                    if not resource_result.data:

                        st.error(
                            "❌ Failed to create resource."
                        )

                    else:

                        resource = resource_result.data[0]

                        resource_id = resource["id"]

                        # ------------------------------------------------
                        # Create resource-channel relationships
                        # ------------------------------------------------

                        relationship_rows = []

                        for channel_name in selected_channel_names:

                            channel_id = channel_options[
                                channel_name
                            ]

                            relationship_rows.append(
                                {
                                    "resource_id": resource_id,
                                    "channel_id": channel_id,
                                }
                            )

                        (
                            supabase
                            .table(
                                "resource_required_channels"
                            )
                            .insert(
                                relationship_rows
                            )
                            .execute()
                        )

                        # ------------------------------------------------
                        # Generate bot deep link
                        # ------------------------------------------------

                        bot_link = (
                            f"https://t.me/"
                            f"{BOT_USERNAME}"
                            f"?start=resource_{resource_id}"
                        )

                        st.success(
                            "✅ Resource created successfully!"
                        )

                        st.write(
                            "**Telegram Download Link:**"
                        )

                        st.code(
                            bot_link
                        )

                        st.info(
                            "Copy this link and add it "
                            "to the corresponding anime "
                            "channel."
                        )

                        st.rerun()

            except Exception as error:

                st.error(
                    f"❌ Database error: {error}"
                )


st.divider()


# ============================================================
# EXISTING RESOURCES
# ============================================================

st.subheader("📋 Existing Resources")


try:

    resources_response = (
        supabase
        .table("resources")
        .select("*")
        .order(
            "created_at",
            desc=True,
        )
        .execute()
    )

    resources = resources_response.data or []

except Exception as error:

    st.error(
        f"❌ Failed to load resources: {error}"
    )

    resources = []


# ============================================================
# NO RESOURCES
# ============================================================

if not resources:

    st.info(
        "No resources have been created yet."
    )


# ============================================================
# DISPLAY RESOURCES
# ============================================================

else:

    for resource in resources:

        resource_id = resource["id"]

        resource_name = resource.get(
            "name",
            "Unnamed Resource",
        )

        resource_drive_url = resource.get(
            "drive_url",
            "",
        )

        resource_active = resource.get(
            "is_active",
            True,
        )

        bot_link = (
            f"https://t.me/"
            f"{BOT_USERNAME}"
            f"?start=resource_{resource_id}"
        )

        with st.container(border=True):

            # ------------------------------------------------
            # Header
            # ------------------------------------------------

            col1, col2, col3 = st.columns(
                [5, 2, 1]
            )

            with col1:

                st.markdown(
                    f"### 🎬 {resource_name}"
                )

            with col2:

                if resource_active:

                    st.success(
                        "Active"
                    )

                else:

                    st.warning(
                        "Inactive"
                    )

            with col3:

                st.write(
                    f"ID: `{resource_id}`"
                )

            # ------------------------------------------------
            # Resource information
            # ------------------------------------------------

            info_col1, info_col2 = st.columns(2)

            with info_col1:

                st.write(
                    "**Google Drive Link**"
                )

                if resource_drive_url:

                    st.code(
                        resource_drive_url
                    )

                else:

                    st.warning(
                        "No Google Drive link"
                    )

            with info_col2:

                st.write(
                    "**Telegram Bot Link**"
                )

                st.code(
                    bot_link
                )

            # ------------------------------------------------
            # Required channels
            # ------------------------------------------------

            st.write(
                "**Required Channels**"
            )

            try:

                required_response = (
                    supabase
                    .table(
                        "resource_required_channels"
                    )
                    .select(
                        """
                        channel_id,
                        telegram_channels (
                            id,
                            name
                        )
                        """
                    )
                    .eq(
                        "resource_id",
                        resource_id,
                    )
                    .execute()
                )

                required_channels = (
                    required_response.data or []
                )

                if required_channels:

                    for row in required_channels:

                        channel = row.get(
                            "telegram_channels"
                        )

                        if channel:

                            st.write(
                                f"📢 {channel['name']}"
                            )

                else:

                    st.write(
                        "No required channels."
                    )

            except Exception as error:

                st.error(
                    f"Failed to load required "
                    f"channels: {error}"
                )

            # ------------------------------------------------
            # Created date
            # ------------------------------------------------

            st.write(
                "**Created:** "
                + str(
                    resource.get(
                        "created_at",
                        "Unknown",
                    )
                )
            )

            # ------------------------------------------------
            # Actions
            # ------------------------------------------------

            st.write("")

            action_col1, action_col2 = st.columns(2)

            with action_col1:

                toggle_text = (
                    "⛔ Disable Resource"
                    if resource_active
                    else "✅ Enable Resource"
                )

                if st.button(
                    toggle_text,
                    key=f"toggle_resource_{resource_id}",
                    use_container_width=True,
                ):

                    try:

                        (
                            supabase
                            .table("resources")
                            .update(
                                {
                                    "is_active": (
                                        not resource_active
                                    )
                                }
                            )
                            .eq(
                                "id",
                                resource_id,
                            )
                            .execute()
                        )

                        st.success(
                            "Resource status updated."
                        )

                        st.rerun()

                    except Exception as error:

                        st.error(
                            f"❌ Failed to update resource: "
                            f"{error}"
                        )

            with action_col2:

                if st.button(
                    "🗑️ Delete Resource",
                    key=f"delete_resource_{resource_id}",
                    use_container_width=True,
                ):

                    try:

                        # Delete relationships first
                        (
                            supabase
                            .table(
                                "resource_required_channels"
                            )
                            .delete()
                            .eq(
                                "resource_id",
                                resource_id,
                            )
                            .execute()
                        )

                        # Delete resource
                        (
                            supabase
                            .table("resources")
                            .delete()
                            .eq(
                                "id",
                                resource_id,
                            )
                            .execute()
                        )

                        st.success(
                            "Resource deleted successfully."
                        )

                        st.rerun()

                    except Exception as error:

                        st.error(
                            f"❌ Failed to delete resource: "
                            f"{error}"
                        )