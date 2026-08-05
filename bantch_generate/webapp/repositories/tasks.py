from ..database.connection import get_connection


def create(request_id, user, model, prompt):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO tasks (
                request_id, user_id, username, model, prompt, api_key_env_var
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (request_id, user["id"], user["username"], model, prompt, user["api_key_env_var"]),
        )
        connection.commit()
        return cursor.lastrowid
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def set_upstream_task_id(task_id, upstream_task_id):
    _update(
        "UPDATE tasks SET upstream_task_id = %s WHERE id = %s",
        (upstream_task_id, task_id),
    )


def complete(task_id, success, status_code, error_message=None):
    _update(
        """
        UPDATE tasks
        SET completed_at = NOW(), is_success = %s, status = %s,
            response_status_code = %s, error_message = %s
        WHERE id = %s
        """,
        (1 if success else 0, "success" if success else "failed", status_code, error_message, task_id),
    )


def list_recent_for_user(user_id, limit=10):
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                id, request_id, upstream_task_id, model, prompt, requested_at,
                completed_at, status, is_success, response_status_code, error_message
            FROM tasks
            WHERE user_id = %s
            ORDER BY requested_at DESC, id DESC
            LIMIT %s
            """,
            (user_id, limit),
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def _update(statement, values):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(statement, values)
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()
