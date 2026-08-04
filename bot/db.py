"""
Supabase database client with error handling.
"""
import os
from typing import Optional, Any
from supabase import create_client, Client
from bot.telegram_notify import notify_admin


class SupabaseDB:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not url or not key:
            notify_admin("Supabase", "❌ Config missing",
                       "SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set", {})
            raise ValueError("Missing Supabase credentials")

        try:
            self.client: Client = create_client(url, key)
        except Exception as e:
            notify_admin("Supabase", "❌ Connection failed",
                       f"Failed to create client: {str(e)}", {})
            raise

    def execute_query(self, query_fn) -> Optional[Any]:
        """
        Execute a Supabase query with error handling.

        Args:
            query_fn: A function that returns a Supabase query builder

        Returns:
            Query result data, or None if failed
        """
        try:
            response = query_fn()
            return response.data
        except Exception as e:
            error_msg = str(e)

            # Classify error
            if "540" in error_msg or "connection refused" in error_msg.lower():
                notify_admin("Supabase", "HTTP 540",
                           "Supabase project paused - restore it in the dashboard",
                           {"error": error_msg[:200]})
            elif "401" in error_msg or "unauthorized" in error_msg.lower():
                notify_admin("Supabase", "HTTP 401",
                           "Authentication failed - check service role key",
                           {"error": error_msg[:200]})
            elif "RLS" in error_msg.upper() or "policy" in error_msg.lower():
                notify_admin("Supabase", "⚠️ RLS violation",
                           error_msg[:300],
                           {})
            else:
                notify_admin("Supabase", "❌ Query failed",
                           error_msg[:300],
                           {})

            return None

    def insert(self, table: str, data: dict) -> Optional[Any]:
        """Insert a row into a table."""
        return self.execute_query(
            lambda: self.client.table(table).insert(data).execute()
        )

    def upsert(self, table: str, data: dict) -> Optional[Any]:
        """Upsert a row (insert or update)."""
        return self.execute_query(
            lambda: self.client.table(table).upsert(data).execute()
        )

    def select(self, table: str, filters: Optional[dict] = None, columns: str = "*") -> Optional[list]:
        """Select rows from a table."""
        def query():
            q = self.client.table(table).select(columns)
            if filters:
                for key, value in filters.items():
                    q = q.eq(key, value)
            return q.execute()

        result = self.execute_query(query)
        return result if result else []

    def update(self, table: str, data: dict, filters: dict) -> Optional[Any]:
        """Update rows in a table."""
        def query():
            q = self.client.table(table).update(data)
            for key, value in filters.items():
                q = q.eq(key, value)
            return q.execute()

        return self.execute_query(query)
