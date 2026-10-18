"""Reset the HR leave database to seed state."""

from server.db import HR_DB_PATH, reset_database


if __name__ == "__main__":
    reset_database()
    print(f"Database reset at {HR_DB_PATH}")
