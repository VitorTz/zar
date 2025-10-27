from src.tables import dashboard as dashboard_view
from src.schemas.dashboard import Dashboard
from asyncpg import Connection
from src.util import minutes_since


async def get_dashboard(conn: Connection) -> Dashboard:
    dashboard: Dashboard = await dashboard_view.get_dashboard(conn)
    if dashboard.last_updated and minutes_since(dashboard.last_updated) >= 60:
        await dashboard_view.refresh_dashboard(conn)
        return await dashboard_view.get_dashboard(conn)
    return dashboard


async def refresh_dashboard(conn: Connection) -> Dashboard:
    await dashboard_view.refresh_dashboard(conn)
    return await dashboard_view.get_dashboard(conn)