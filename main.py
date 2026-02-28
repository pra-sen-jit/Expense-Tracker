"""
Main entry point for the Expense Tracker application.

Before running this application, ensure that:
1. Install dependencies: pip install -r requirements.txt
2. Set up environment variable: export DATABASE_URL="postgresql://user:password@host/database"
   (Or create a .env file based on .env.example)
3. Run the application: python main.py

The application will:
- Load DATABASE_URL from environment variables
- Connect to the PostgreSQL database on Neon
- Create the expenses table and trigger if they don't exist
- Launch the GUI application
"""

import os
import sys
import logging
from dotenv import load_dotenv
from PySide6.QtWidgets import QApplication, QMessageBox
from db import DatabaseManager
from ui import ExpenseTrackerUI
from psycopg2 import Error

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('expense_tracker.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """
    Initialize and run the Expense Tracker application.

    Steps:
    1. Load DATABASE_URL from environment
    2. Initialize database manager (creates pool and schema)
    3. Create and show the main window
    4. Run the application event loop
    """
    logger.info("Starting Expense Tracker application")

    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')

    if not database_url:
        logger.error("DATABASE_URL environment variable not found")
        print("ERROR: DATABASE_URL environment variable is not set.")
        print("\nTo set it up:")
        print("1. Copy .env.example to .env")
        print("2. Edit .env with your Neon database URL")
        print("3. Run: python main.py")
        sys.exit(1)

    # Initialize Qt Application
    app = QApplication(sys.argv)

    try:
        # Initialize database manager
        logger.info("Initializing database connection...")
        db_manager = DatabaseManager(database_url)

        # Create and show main window
        logger.info("Creating main window...")
        window = ExpenseTrackerUI(db_manager)
        window.show()

        logger.info("Application started successfully")

        # Run event loop
        sys.exit(app.exec())

    except Error as e:
        logger.error(f"Database connection failed: {e}")
        QMessageBox.critical(
            None,
            "Database Connection Error",
            f"Failed to connect to database:\n{str(e)}\n\n"
            "Please check your DATABASE_URL environment variable."
        )
        sys.exit(1)

    except Exception as e:
        logger.error(f"Application error: {e}")
        QMessageBox.critical(
            None,
            "Application Error",
            f"An unexpected error occurred:\n{str(e)}"
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
