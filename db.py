"""
Database module for Expense Tracker application.

Handles:
- PostgreSQL connection management
- Table and trigger creation
- Query execution with parameterized statements
- Connection pooling
"""

import logging
import psycopg2
from psycopg2 import pool, Error
from typing import List, Tuple, Dict, Any

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database connections and operations."""

    def __init__(self, database_url: str, min_connections: int = 1, max_connections: int = 5):
        """
        Initialize the database manager with connection pooling.

        Args:
            database_url: PostgreSQL connection URL (e.g., postgresql://user:pass@host/db)
            min_connections: Minimum connections in the pool
            max_connections: Maximum connections in the pool
        """
        self.database_url = database_url
        self.connection_pool = None
        self._initialize_pool(min_connections, max_connections)
        self._initialize_schema()

    def _initialize_pool(self, min_connections: int, max_connections: int) -> None:
        """Create a connection pool for database operations."""
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                min_connections,
                max_connections,
                self.database_url
            )
            logger.info("Database connection pool initialized successfully")
        except Error as e:
            logger.error(f"Failed to initialize connection pool: {e}")
            raise

    def _initialize_schema(self) -> None:
        """Create table and trigger if they don't exist."""
        try:
            self._execute_statement(self._get_create_table_sql())
            logger.info("Expenses table created or already exists")

            self._execute_statement(self._get_create_trigger_sql())
            logger.info("Trigger for updated_at column created or already exists")
        except Error as e:
            logger.error(f"Failed to initialize schema: {e}")
            raise

    @staticmethod
    def _get_create_table_sql() -> str:
        """Return the SQL to create the expenses table."""
        return """
        CREATE TABLE IF NOT EXISTS expenses (
            id BIGSERIAL PRIMARY KEY,
            expense_date DATE NOT NULL,
            amount NUMERIC(10,2) NOT NULL CHECK (amount >= 0),
            category VARCHAR(100) NOT NULL,
            payment_method VARCHAR(100) NOT NULL,
            description VARCHAR(255),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

    @staticmethod
    def _get_create_trigger_sql() -> str:
        """Return the SQL to create a trigger for auto-updating updated_at."""
        return """
        CREATE OR REPLACE FUNCTION update_expenses_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        DROP TRIGGER IF EXISTS expenses_updated_at_trigger ON expenses;

        CREATE TRIGGER expenses_updated_at_trigger
        BEFORE UPDATE ON expenses
        FOR EACH ROW
        EXECUTE FUNCTION update_expenses_updated_at();
        """

    def get_connection(self):
        """Get a connection from the pool."""
        if self.connection_pool is None:
            raise RuntimeError("Connection pool not initialized")
        return self.connection_pool.getconn()

    def return_connection(self, conn):
        """Return a connection to the pool."""
        if self.connection_pool and conn:
            self.connection_pool.putconn(conn)

    def _execute_statement(self, statement: str, params: Tuple = None) -> None:
        """
        Execute a non-SELECT statement (CREATE, INSERT, UPDATE, DELETE).
        Internal method for schema operations and data modifications.

        Args:
            statement: SQL statement to execute
            params: Query parameters for parameterized queries

        Raises:
            Error: If database operation fails
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            if params:
                cursor.execute(statement, params)
            else:
                cursor.execute(statement)

            conn.commit()
            cursor.close()

            logger.debug(f"Statement executed successfully")

        except Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Database statement failed: {e}")
            raise
        finally:
            if conn:
                self.return_connection(conn)

    def execute_query(self, query: str, params: Tuple = None) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results.

        Args:
            query: SQL query string
            params: Query parameters for parameterized queries

        Returns:
            List of dictionaries representing query results

        Raises:
            ValueError: If query is not a SELECT statement
            Error: If database operation fails
        """
        # Security: Only allow SELECT queries
        if not self._is_select_query(query):
            raise ValueError("Only SELECT queries are allowed")

        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            # Fetch column names
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()

            # Convert to list of dictionaries
            results = [dict(zip(columns, row)) for row in rows]
            cursor.close()

            logger.info(f"Query executed successfully, returned {len(results)} rows")
            return results

        except Error as e:
            logger.error(f"Database query failed: {e}")
            raise
        finally:
            if conn:
                self.return_connection(conn)

    def insert_expense(
        self,
        expense_date: str,
        amount: float,
        category: str,
        payment_method: str,
        description: str = None,
        notes: str = None
    ) -> int:
        """
        Insert a new expense record.

        Args:
            expense_date: Date in YYYY-MM-DD format
            amount: Expense amount
            category: Expense category
            payment_method: Payment method used
            description: Optional description
            notes: Optional notes

        Returns:
            ID of the inserted record

        Raises:
            Error: If insertion fails
        """
        query = """
        INSERT INTO expenses (expense_date, amount, category, payment_method, description, notes)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id;
        """

        params = (expense_date, amount, category, payment_method, description, notes)

        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            expense_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()

            logger.info(f"Expense record inserted with ID: {expense_id}")
            return expense_id

        except Error as e:
            if conn:
                conn.rollback()
            logger.error(f"Failed to insert expense: {e}")
            raise
        finally:
            if conn:
                self.return_connection(conn)

    def get_monthly_totals_by_year(self, year: int) -> List[Dict[str, Any]]:
        """
        Return monthly expense totals for a given year.

        Args:
            year: Calendar year (e.g., 2026)

        Returns:
            List of rows with keys: month, total_amount
        """
        query = """
        SELECT
            EXTRACT(MONTH FROM expense_date)::INT AS month,
            COALESCE(SUM(amount), 0)::NUMERIC(10,2) AS total_amount
        FROM expenses
        WHERE EXTRACT(YEAR FROM expense_date)::INT = %s
        GROUP BY month
        ORDER BY month;
        """
        return self.execute_query(query, (year,))

    @staticmethod
    def _is_select_query(query: str) -> bool:
        """
        Check if query is a SELECT statement.

        Args:
            query: SQL query string

        Returns:
            True if query is a SELECT statement, False otherwise
        """
        cleaned = query.strip().upper()
        return cleaned.startswith("SELECT")

    def close(self) -> None:
        """Close all connections in the pool."""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("All database connections closed")
