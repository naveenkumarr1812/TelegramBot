from database import supabase


if __name__ == "__main__":
    response = supabase.table("resources").select("*").limit(10).execute()
    print(response.data)
