from database import supabase


def save_user(user):

    data = {
        "telegram_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
    }

    (
        supabase
        .table("users")
        .upsert(
            data,
            on_conflict="telegram_id",
        )
        .execute()
    )