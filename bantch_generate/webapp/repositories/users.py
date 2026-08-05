from ..database.connection import get_connection


USER_COLUMNS = "id, username, password_hash, role, api_key_env_var, is_active, created_at"


def get_by_username(username):
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(f"SELECT {USER_COLUMNS} FROM users WHERE username = %s LIMIT 1", (username,))
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()


def get_by_id(user_id):
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(f"SELECT {USER_COLUMNS} FROM users WHERE id = %s LIMIT 1", (user_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()


def create(username, password_hash, role, api_key_env_var):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO users (username, password_hash, role, api_key_env_var)
            VALUES (%s, %s, %s, %s)
            """,
            (username, password_hash, role, api_key_env_var),
        )
        connection.commit()
        return cursor.lastrowid
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def list_all():
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT id, username, role, api_key_env_var, is_active, created_at
            FROM users
            ORDER BY created_at DESC, id DESC
            """
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def update_password(user_id, password_hash):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE id = %s",
            (password_hash, user_id),
        )
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()
