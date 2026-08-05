from ..database.connection import get_connection


def create(task_id, user, prompt, image_path, source_url, raw_response_json, model):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO results (
                task_id, user_id, username, prompt, image_path, source_url,
                raw_response_json, model
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                task_id,
                user["id"],
                user["username"],
                prompt,
                image_path,
                source_url,
                raw_response_json,
                model,
            ),
        )
        connection.commit()
        return cursor.lastrowid
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def create_many(task_id, user, prompt, stored_items, raw_response_json, model):
    connection = get_connection()
    try:
        cursor = connection.cursor()
        result_ids = []
        for item in stored_items:
            cursor.execute(
                """
                INSERT INTO results (
                    task_id, user_id, username, prompt, image_path, source_url,
                    raw_response_json, model
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    task_id,
                    user["id"],
                    user["username"],
                    prompt,
                    item["image_path"],
                    item["source_url"],
                    raw_response_json,
                    model,
                ),
            )
            result_ids.append(cursor.lastrowid)
        connection.commit()
        return result_ids
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def get_by_id(result_id):
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT * FROM results WHERE id = %s LIMIT 1", (result_id,))
        return cursor.fetchone()
    finally:
        cursor.close()
        connection.close()


def list_for_task_ids(task_ids):
    if not task_ids:
        return []
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        placeholders = ", ".join(["%s"] * len(task_ids))
        cursor.execute(
            f"""
            SELECT id, task_id, model, created_at
            FROM results
            WHERE task_id IN ({placeholders})
            ORDER BY id ASC
            """,
            tuple(task_ids),
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def usage_summary():
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT
                u.id AS user_id,
                u.username,
                u.role,
                COUNT(DISTINCT t.id) AS successful_requests,
                MAX(CASE WHEN t.id IS NOT NULL THEN r.created_at END) AS last_success_at
            FROM users u
            LEFT JOIN results r ON r.user_id = u.id
            LEFT JOIN tasks t ON t.id = r.task_id AND t.is_success = 1
            GROUP BY u.id, u.username, u.role
            ORDER BY successful_requests DESC, u.username ASC
            """
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def model_usage_summary():
    connection = get_connection()
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            """
            SELECT r.username, r.model, COUNT(DISTINCT r.task_id) AS successful_requests
            FROM results r
            INNER JOIN tasks t ON t.id = r.task_id AND t.is_success = 1
            GROUP BY r.username, r.model
            ORDER BY r.username ASC, successful_requests DESC, r.model ASC
            """
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()
