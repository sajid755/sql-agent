from langchain.tools import tool
from db_config import get_connection
from tabulate import tabulate
import csv
import os
from datetime import datetime

@tool
def run_sql_query(query: str) -> str:
    """Run a SQL query and return up to 20 rows. If more rows exist, suggests using export_query_to_csv tool."""
    print(f"\n[SQL Query]: {query}\n")
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Fetch only 21 rows to check if there are more
                cur.execute(query)
                rows = cur.fetchmany(21)
                columns = [desc[0] for desc in cur.description] if cur.description else []

        if not rows:
            return "Query executed successfully. No rows returned."

        has_more = len(rows) > 20

        # If more than 20 rows exist, show first 20 and suggest CSV export
        if has_more:
            display_rows = rows[:20]
            table = tabulate(display_rows, headers=columns, tablefmt="psql")
            return f"Showing first 20 rows (more rows available).\n\nTo get all results, ask me to export to CSV using export_query_to_csv tool.\n\n{table}"

        return tabulate(rows, headers=columns, tablefmt="psql")
    except Exception as e:
        return f"[Error]: {e}"
    finally:
        conn.close()


@tool
def get_table_schema(table_name: str) -> str:
    """Get the schema (columns + datatypes) of a PostgreSQL table."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                
                # Parameterized to avoid SQL injection
                query = """
                    SELECT 
                        column_name,
                        data_type,
                        character_maximum_length,
                        is_nullable,
                        column_default
                    FROM information_schema.columns
                    WHERE table_name = %s
                    ORDER BY ordinal_position;
                """

                cur.execute(query, (table_name,))
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description]

        # --- Pretty Print Table ---
        col_widths = [max(len(str(row[i])) for row in rows + [columns]) for i in range(len(columns))]

        header = " | ".join(columns[i].ljust(col_widths[i]) for i in range(len(columns)))
        separator = "-+-".join("-" * col_widths[i] for i in range(len(columns)))

        output = [header, separator]

        for row in rows:
            output.append(" | ".join(str(row[i]).ljust(col_widths[i]) for i in range(len(columns))))

        return "\n".join(output)

    except Exception as e:
        return f"[Error]: {e}"
    finally:
        conn.close()


@tool
def list_tables(schema: str = "public", pattern: str = None, limit: int = 50, offset: int = 0) -> str:
    """List table names in the database with optional filtering and pagination.

    Args:
        schema: Database schema (default: 'public')
        pattern: SQL LIKE pattern for filtering (e.g., 'user_%', '%customer%')
        limit: Maximum number of tables to return (default: 50)
        offset: Starting position for pagination (default: 0)

    Examples:
        list_tables() - First 50 tables
        list_tables(pattern="test_%") - Tables starting with 'test_'
        list_tables(pattern="%customer%") - Tables containing 'customer'
        list_tables(limit=100) - First 100 tables
        list_tables(offset=50, limit=50) - Tables 51-100
    """

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                # Build query with optional pattern filter
                if pattern:
                    count_query = """
                        SELECT COUNT(*)
                        FROM information_schema.tables
                        WHERE table_schema = %s AND table_name LIKE %s;
                    """
                    query = """
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = %s AND table_name LIKE %s
                        ORDER BY table_name
                        LIMIT %s OFFSET %s;
                    """
                    cur.execute(count_query, (schema, pattern))
                    total_count = cur.fetchone()[0]
                    cur.execute(query, (schema, pattern, limit, offset))
                else:
                    count_query = """
                        SELECT COUNT(*)
                        FROM information_schema.tables
                        WHERE table_schema = %s;
                    """
                    query = """
                        SELECT table_name
                        FROM information_schema.tables
                        WHERE table_schema = %s
                        ORDER BY table_name
                        LIMIT %s OFFSET %s;
                    """
                    cur.execute(count_query, (schema,))
                    total_count = cur.fetchone()[0]
                    cur.execute(query, (schema, limit, offset))

                tables = cur.fetchall()

        if total_count == 0:
            if pattern:
                return f"No tables found in schema '{schema}' matching pattern '{pattern}'."
            return f"No tables found in schema '{schema}'."

        # Build output
        result = []

        # Header with pagination info
        start = offset + 1
        end = min(offset + len(tables), total_count)

        if pattern:
            result.append(f"Tables matching '{pattern}': Showing {start}-{end} of {total_count} total")
        else:
            result.append(f"Tables in schema '{schema}': Showing {start}-{end} of {total_count} total")

        result.append("")

        # Table list
        result.extend(t[0] for t in tables)

        # Pagination hints
        if end < total_count:
            result.append("")
            result.append(f"--- More tables available ({total_count - end} remaining) ---")
            next_offset = offset + limit
            if pattern:
                result.append(f"Use list_tables(pattern='{pattern}', offset={next_offset}, limit={limit}) to see next page")
            else:
                result.append(f"Use list_tables(offset={next_offset}, limit={limit}) to see next page")

        return "\n".join(result)

    except Exception as e:
        return f"[Error]: {e}"
    finally:
        conn.close()


@tool
def export_query_to_csv(query: str, filename: str = None) -> str:
    """Execute a SQL query and export the results to a CSV file.
    If no filename is provided, generates one with timestamp."""

    print(f"\n[SQL Query for Export]: {query}\n")

    try:
        # Generate filename if not provided
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"query_export_{timestamp}.csv"

        # Ensure .csv extension
        if not filename.endswith('.csv'):
            filename += '.csv'

        # Create output directory if it doesn't exist
        output_dir = "exports"
        os.makedirs(output_dir, exist_ok=True)
        filepath = os.path.join(output_dir, filename)

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                rows = cur.fetchall()
                columns = [desc[0] for desc in cur.description] if cur.description else []

        if not rows:
            return "Query executed successfully but returned no rows. No CSV created."

        # Write to CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(columns)  # Write header
            writer.writerows(rows)     # Write data

        row_count = len(rows)
        print(f"[CSV Export]: Exported {row_count} rows to {filepath}\n")
        return f"Successfully exported {row_count} rows to {filepath}"

    except Exception as e:
        return f"[Error]: {e}"
    finally:
        conn.close()

