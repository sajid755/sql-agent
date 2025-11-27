"""
Populate empty test tables with data
"""

import os
import psycopg2
from dotenv import load_dotenv
from faker import Faker
import random
from datetime import timedelta

load_dotenv()
fake = Faker()

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )

def populate_table(conn, table_name, count=50):
    """Populate a single table with fake data"""
    cursor = conn.cursor()

    try:
        if 'customers' in table_name:
            for _ in range(count):
                cursor.execute(f"""
                    INSERT INTO {table_name} (name, email, phone, country, registration_date, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (fake.name()[:100], fake.email()[:100], fake.phone_number()[:20], fake.country()[:50],
                      fake.date_between(start_date='-2y', end_date='today'),
                      random.choice(['active', 'inactive', 'pending'])))

        elif 'products' in table_name:
            for _ in range(count):
                cursor.execute(f"""
                    INSERT INTO {table_name} (product_name, category, price, stock_quantity, manufacturer, release_date)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (fake.catch_phrase()[:200], random.choice(['Electronics', 'Clothing', 'Food', 'Books', 'Toys'])[:50],
                      round(random.uniform(10, 1000), 2), random.randint(0, 500),
                      fake.company()[:100], fake.date_between(start_date='-3y', end_date='today')))

        elif 'orders' in table_name:
            for _ in range(count):
                cursor.execute(f"""
                    INSERT INTO {table_name} (order_number, customer_name, total_amount, order_date, status, shipping_address)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (fake.uuid4()[:8], fake.name()[:100], round(random.uniform(20, 5000), 2),
                      fake.date_time_between(start_date='-1y', end_date='now'),
                      random.choice(['pending', 'shipped', 'delivered', 'cancelled'])[:30],
                      fake.address()))

        elif 'employees' in table_name:
            for _ in range(count):
                cursor.execute(f"""
                    INSERT INTO {table_name} (first_name, last_name, department, position, salary, hire_date, manager_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (fake.first_name()[:50], fake.last_name()[:50],
                      random.choice(['IT', 'Sales', 'HR', 'Finance', 'Marketing', 'Operations'])[:50],
                      fake.job()[:100], round(random.uniform(40000, 150000), 2),
                      fake.date_between(start_date='-10y', end_date='today'), fake.name()[:100]))

        elif 'transactions' in table_name:
            for _ in range(count):
                cursor.execute(f"""
                    INSERT INTO {table_name} (transaction_id, amount, transaction_type, timestamp, description, category)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (fake.uuid4()[:12], round(random.uniform(-1000, 5000), 2),
                      random.choice(['credit', 'debit', 'transfer', 'refund'])[:30],
                      fake.date_time_between(start_date='-6m', end_date='now'),
                      fake.sentence(), random.choice(['salary', 'purchase', 'service', 'subscription'])[:50]))

        elif 'inventory' in table_name:
            for _ in range(count):
                cursor.execute(f"""
                    INSERT INTO {table_name} (item_code, item_name, warehouse_location, quantity, unit_price, last_restocked)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (fake.bothify('ITM-####')[:50], fake.catch_phrase()[:200],
                      f"Warehouse-{random.choice(['A', 'B', 'C'])}-{random.randint(1, 50)}"[:50],
                      random.randint(0, 1000), round(random.uniform(5, 500), 2),
                      fake.date_between(start_date='-1y', end_date='today')))

        elif 'events' in table_name:
            for _ in range(count):
                start = fake.date_time_between(start_date='-6m', end_date='+6m')
                end = start + timedelta(hours=random.randint(1, 8))
                cursor.execute(f"""
                    INSERT INTO {table_name} (event_name, event_type, location, start_time, end_time, attendees, organizer)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (fake.catch_phrase()[:200], random.choice(['Conference', 'Workshop', 'Seminar', 'Meeting', 'Social'])[:50],
                      fake.city()[:100], start, end, random.randint(10, 500), fake.name()[:100]))

        elif 'analytics' in table_name:
            for _ in range(count):
                cursor.execute(f"""
                    INSERT INTO {table_name} (metric_name, metric_value, dimension, timestamp, source)
                    VALUES (%s, %s, %s, %s, %s)
                """, (random.choice(['page_views', 'conversions', 'revenue', 'bounce_rate', 'session_duration'])[:100],
                      round(random.uniform(0, 10000), 2),
                      random.choice(['mobile', 'desktop', 'tablet'])[:50],
                      fake.date_time_between(start_date='-3m', end_date='now'),
                      random.choice(['google', 'facebook', 'direct', 'email'])[:50]))

        elif 'projects' in table_name:
            for _ in range(count):
                start = fake.date_between(start_date='-2y', end_date='today')
                deadline = start + timedelta(days=random.randint(30, 365))
                cursor.execute(f"""
                    INSERT INTO {table_name} (project_name, client_name, start_date, deadline, budget, status, team_size)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (fake.catch_phrase()[:200], fake.company()[:100], start, deadline,
                      round(random.uniform(10000, 500000), 2),
                      random.choice(['planning', 'in_progress', 'completed', 'on_hold'])[:30],
                      random.randint(2, 20)))

        elif 'reviews' in table_name:
            for _ in range(count):
                cursor.execute(f"""
                    INSERT INTO {table_name} (reviewer_name, rating, review_text, review_date, product_name, helpful_count)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (fake.name()[:100], random.randint(1, 5), fake.paragraph(),
                      fake.date_between(start_date='-1y', end_date='today'),
                      fake.catch_phrase()[:200], random.randint(0, 100)))

        conn.commit()
        return True
    except Exception as e:
        print(f"[ERROR] {table_name}: {e}")
        conn.rollback()
        return False

def main():
    conn = get_connection()
    cursor = conn.cursor()

    # Find empty tables
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name LIKE 'test_%'
        ORDER BY table_name
    """)

    all_tables = [row[0] for row in cursor.fetchall()]

    empty_tables = []
    for table in all_tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        if count == 0:
            empty_tables.append(table)

    print(f"Found {len(empty_tables)} empty tables out of {len(all_tables)} total test tables")
    print("Populating empty tables...\n")

    success = 0
    for i, table in enumerate(empty_tables, 1):
        if populate_table(conn, table, 50):
            success += 1
        if i % 10 == 0:
            print(f"[OK] Populated {i}/{len(empty_tables)} tables...")

    print(f"\n[OK] Successfully populated {success}/{len(empty_tables)} tables!")
    conn.close()

if __name__ == "__main__":
    main()
