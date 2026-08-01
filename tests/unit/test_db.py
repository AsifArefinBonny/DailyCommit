"""
Unit tests for Supabase database client
Tests CRUD operations, error handling, and data validation
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from bot.db import SupabaseDB


class TestSupabaseDB:
    """Test SupabaseDB functionality"""

    @patch('bot.db.create_client')
    def setup_method(self, mock_create_client):
        """Set up test fixtures"""
        self.mock_client = Mock()
        mock_create_client.return_value = self.mock_client

        with patch.dict('os.environ', {
            'SUPABASE_URL': 'https://test.supabase.co',
            'SUPABASE_SERVICE_ROLE_KEY': 'test_key'
        }):
            self.db = SupabaseDB()

    def test_initialization(self):
        """Test database client initialization"""
        assert self.db.client is not None

    def test_select_all(self):
        """Test selecting all records from a table"""
        # Mock Supabase response
        mock_table = Mock()
        mock_table.select.return_value.execute.return_value.data = [
            {"id": "1", "name": "Test"},
            {"id": "2", "name": "Test2"}
        ]
        self.mock_client.table.return_value = mock_table

        results = self.db.select("test_table")

        assert len(results) == 2
        assert results[0]["name"] == "Test"

    def test_select_with_filters(self):
        """Test selecting with filters"""
        mock_table = Mock()
        mock_execute = Mock()
        mock_execute.data = [{"id": "1", "name": "Test"}]

        mock_table.select.return_value.eq.return_value.execute.return_value = mock_execute
        self.mock_client.table.return_value = mock_table

        results = self.db.select("test_table", filters={"id": "1"})

        assert len(results) == 1
        assert results[0]["id"] == "1"

    def test_insert_single_record(self):
        """Test inserting a single record"""
        mock_table = Mock()
        mock_execute = Mock()
        mock_execute.data = [{"id": "1", "name": "New"}]

        mock_table.insert.return_value.execute.return_value = mock_execute
        self.mock_client.table.return_value = mock_table

        result = self.db.insert("test_table", {"name": "New"})

        assert result is not None
        assert result[0]["name"] == "New"

    def test_update_record(self):
        """Test updating a record"""
        mock_table = Mock()
        mock_execute = Mock()
        mock_execute.data = [{"id": "1", "name": "Updated"}]

        mock_table.update.return_value.eq.return_value.execute.return_value = mock_execute
        self.mock_client.table.return_value = mock_table

        result = self.db.update("test_table", {"id": "1"}, {"name": "Updated"})

        assert result is not None
        assert result[0]["name"] == "Updated"

    def test_upsert_record(self):
        """Test upserting a record"""
        mock_table = Mock()
        mock_execute = Mock()
        mock_execute.data = [{"id": "1", "name": "Upserted"}]

        mock_table.upsert.return_value.execute.return_value = mock_execute
        self.mock_client.table.return_value = mock_table

        result = self.db.upsert("test_table", {"id": "1", "name": "Upserted"})

        assert result is not None
        assert result[0]["name"] == "Upserted"

    def test_delete_record(self):
        """Test deleting a record"""
        mock_table = Mock()
        mock_execute = Mock()
        mock_execute.data = [{"id": "1"}]

        mock_table.delete.return_value.eq.return_value.execute.return_value = mock_execute
        self.mock_client.table.return_value = mock_table

        result = self.db.delete("test_table", {"id": "1"})

        assert result is not None

    def test_error_handling_select(self):
        """Test error handling on select"""
        mock_table = Mock()
        mock_table.select.side_effect = Exception("Database error")
        self.mock_client.table.return_value = mock_table

        results = self.db.select("test_table")

        assert results == []  # Should return empty list on error

    def test_error_handling_insert(self):
        """Test error handling on insert"""
        mock_table = Mock()
        mock_table.insert.side_effect = Exception("Insert failed")
        self.mock_client.table.return_value = mock_table

        result = self.db.insert("test_table", {"name": "Fail"})

        assert result is None  # Should return None on error
