from db.supabase_client import get_supabase


def get_all_apps(sb):
    res = sb.table("portfolio_apps").select("*").order("name").execute()
    return res.data or []


def get_app_projects(sb, app_name):
    res = (
        sb.table("projects")
        .select("*")
        .eq("company", "DTSM")
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


def get_active_projects_all(sb):
    res = (
        sb.table("projects")
        .select("*")
        .eq("status", "active")
        .eq("company", "DTSM")
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []
