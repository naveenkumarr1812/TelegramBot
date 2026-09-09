from database import supabase

def get_resource(resource_id: int):

    response = (
        supabase
        .table("resources")
        .select("*")
        .eq("id", resource_id)
        .eq("is_active", True)
        .maybe_single()
        .execute()
    )

    return response.data

def parse_resource_parameter(parameter: str):

    if not parameter:
        return None

    if not parameter.startswith("resource_"):
        return None

    resource_id = parameter.replace(
        "resource_",
        "",
        1
    )

    if not resource_id.isdigit():
        return None

    return int(resource_id)


def get_required_channels(resource_id: int):

    response = (
        supabase
        .table("resource_required_channels")
        .select(
            """
            channel_id,
            telegram_channels (
                id,
                name,
                chat_id,
                username,
                invite_link,
                is_active
            )
            """
        )
        .eq("resource_id", resource_id)
        .execute()
    )

    channels = []

    for row in response.data:

        channel = row.get("telegram_channels")

        if channel and channel["is_active"]:
            channels.append(channel)

    return channels