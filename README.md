# Expense Tracker Desktop Application

A production-ready personal expense tracker desktop application built with Python, PySide6, and PostgreSQL.

## Features

- ✅ Desktop GUI built with PySide6 (Qt for Python)
- ✅ PostgreSQL database connection with connection pooling
- ✅ Automatic table and trigger creation
- ✅ Add new expense records with form validation
- ✅ Execute custom SQL SELECT queries
- ✅ Display query results in a table view
- ✅ Parameterized queries to prevent SQL injection
- ✅ Error handling and logging
- ✅ Clean modular architecture
- ✅ Environment-based configuration

## Prerequisites

- Python 3.11 or higher
- PostgreSQL database (or Neon serverless Postgres)
- pip (Python package manager)

## Installation

### 1. Clone or navigate to the project directory

```bash
cd Expense-Tracker
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

**Option A: Using .env file (recommended)**

```bash
# Copy the example file
cp .env.example .env

# Edit .env with your database URL
# DATABASE_URL=postgresql://username:password@host.neon.tech/database?sslmode=require
```

**Option B: Export environment variable**

```bash
# On Linux/macOS:
export DATABASE_URL="postgresql://username:password@host.neon.tech/database?sslmode=require"

# On Windows (PowerShell):
$env:DATABASE_URL="postgresql://username:password@host.neon.tech/database?sslmode=require"
```

### 4. Get your Neon Database URL

1. Go to [Neon Console](https://console.neon.tech)
2. Create a new project or select an existing one
3. Click "Connection string" and copy the PostgreSQL URL
4. The URL format should be: `postgresql://user:password@host.neon.tech/database?sslmode=require`

## Running the Application

```bash
python main.py
```

The application will:

1. Load the DATABASE_URL from environment variables
2. Connect to your PostgreSQL database
3. Create the `expenses` table if it doesn't exist
4. Create a trigger for auto-updating the `updated_at` column
5. Launch the GUI window

## Database Schema

The application creates the following table:

```sql
CREATE TABLE expenses (
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
```

A trigger automatically updates the `updated_at` timestamp on any record update.

## Usage

### Adding an Expense

1. Fill in the form on the left side:
   - **Expense Date**: Select the date of the expense
   - **Amount**: Enter the expense amount
   - **Category**: e.g., "Food", "Transportation", "Utilities"
   - **Payment Method**: e.g., "Cash", "Credit Card", "Debit Card"
   - **Description** (optional): Brief description of the expense
   - **Notes** (optional): Additional notes

2. Click **"Add Expense"** button
3. You'll see a success message if the expense is added

### Running Queries

1. Enter a **SELECT query** in the "Custom SQL" text area on the right:

   ```sql
   SELECT * FROM expenses WHERE amount > 50 ORDER BY expense_date DESC;
   ```

2. Click **"Run Query"** button
3. Results will be displayed in the table below

**Note**: Only SELECT queries are allowed for security reasons.

## Project Structure

```
Expense-Tracker/
├── main.py           # Application entry point
├── db.py             # Database connection and operations
├── ui.py             # GUI components and logic
├── requirements.txt  # Python dependencies
├── .env.example      # Environment variable template
├── .env              # Environment variables (create from .env.example)
├── expense_tracker.log  # Application logs (created at runtime)
└── README.md         # This file
```

## Security Features

- ✅ **Parameterized Queries**: All user inputs are safely parameterized to prevent SQL injection
- ✅ **SELECT-Only Queries**: Only SELECT statements are allowed in the query executor
- ✅ **Environment Variables**: Database credentials are loaded from environment, not hardcoded
- ✅ **Connection Pooling**: Efficient and secure connection management
- ✅ **Error Handling**: Graceful error messages without exposing sensitive information

## Logging

The application logs all operations to:

- **Console**: Real-time output
- **File**: `expense_tracker.log` (created in the application directory)

Log levels:

- `INFO`: General application flow
- `WARNING`: Validation or user errors
- `ERROR`: Database or critical errors

## Error Handling

The application handles common errors gracefully:

- Invalid environment variables
- Database connection failures
- SQL syntax errors
- Missing required fields
- Invalid data types

All errors are displayed to the user in a user-friendly format.

## Example Queries

```sql
-- Get all expenses for a specific month
SELECT * FROM expenses WHERE expense_date >= '2026-01-01' AND expense_date < '2026-02-01';

-- Get spending by category
SELECT category, SUM(amount) as total FROM expenses GROUP BY category ORDER BY total DESC;

-- Get largest expenses
SELECT expense_date, category, amount, description FROM expenses ORDER BY amount DESC LIMIT 10;

-- Get average spending per day
SELECT AVG(amount) as avg_daily_spending FROM expenses;

-- Get payment methods used
SELECT COUNT(*) as count, payment_method FROM expenses GROUP BY payment_method;
```

## Troubleshooting

### Connection Error: "could not translate host name"

- Check your DATABASE_URL is correct
- Ensure you have internet connection to reach Neon servers
- Verify the hostname is correct

### Connection Error: "password authentication failed"

- Check your username and password in DATABASE_URL
- Ensure the account has access to the database

### Table Not Found Error

- The application creates the table automatically
- Check the logs in `expense_tracker.log` for more details
- Ensure you have CREATE TABLE permissions

### Query Errors

- Only SELECT queries are allowed
- Check SQL syntax
- Use the query examples above as reference

## Production Deployment

This application is suitable for personal desktop use. For production deployment with multiple users:

1. Implement user authentication
2. Add more granular error logging
3. Implement backup strategies
4. Add data validation rules
5. Consider rate limiting for queries
6. Implement audit logging

## Dependencies

- **PySide6**: Qt framework for Python GUI (v6.6.1)
- **psycopg2-binary**: PostgreSQL database adapter (v2.9.9)
- **python-dotenv**: Environment variable loader (v1.0.0)

## License

This is a personal project. Use as needed.

## Support

For issues or questions, check:

1. Application logs: `expense_tracker.log`
2. Database connection settings in `.env`
3. Python version: `python --version` (should be 3.11+)
4. Dependencies: `pip list | grep -E "PySide6|psycopg2|python-dotenv"`
