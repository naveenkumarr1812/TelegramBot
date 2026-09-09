from database import supabase


response = (
    supabase
    .table("resources")
    .select("*")
    .execute()
)

print(response.data)