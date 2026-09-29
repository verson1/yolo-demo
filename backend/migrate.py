"""Apply the safety-helmet columns to a database created by the generic template."""

from pathlib import Path

from db import connection


def main() -> None:
    with connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SHOW COLUMNS FROM detect_record LIKE 'model_id'")
            if cursor.fetchone():
                print("Helmet schema already applied.")
                return
            migration = Path(__file__).resolve().parent / "migrations" / "001_helmet_project.sql"
            statement = migration.read_text(encoding="utf-8").split("ALTER TABLE", 1)[1].strip().rstrip(";")
            cursor.execute("ALTER TABLE " + statement)
    print("Helmet schema applied. Existing records are marked legacy.")


if __name__ == "__main__":
    main()
