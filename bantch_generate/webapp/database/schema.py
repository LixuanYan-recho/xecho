from werkzeug.security import generate_password_hash

from ..config import (
    DEFAULT_SUPERADMIN_KEY_ENV,
    DEFAULT_SUPERADMIN_PASSWORD,
    DEFAULT_SUPERADMIN_USERNAME,
    MYSQL_DATABASE,
    ROLE_SUPER_ADMIN,
)
from .connection import get_connection


TABLE_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS users (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        username VARCHAR(64) NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        role ENUM('user', 'admin', 'super_admin') NOT NULL DEFAULT 'user',
        api_key_env_var VARCHAR(128) NOT NULL,
        is_active TINYINT(1) NOT NULL DEFAULT 1,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        PRIMARY KEY (id),
        UNIQUE KEY uq_users_username (username)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS tasks (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        request_id CHAR(32) NOT NULL,
        upstream_task_id VARCHAR(255) NULL,
        user_id BIGINT UNSIGNED NOT NULL,
        username VARCHAR(64) NOT NULL,
        model VARCHAR(100) NOT NULL,
        prompt LONGTEXT NOT NULL,
        api_key_env_var VARCHAR(128) NOT NULL,
        requested_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        completed_at DATETIME NULL,
        is_success TINYINT(1) NULL,
        status VARCHAR(32) NOT NULL DEFAULT 'processing',
        response_status_code INT NULL,
        error_message LONGTEXT NULL,
        PRIMARY KEY (id),
        UNIQUE KEY uq_tasks_request_id (request_id),
        KEY idx_tasks_user_id (user_id),
        KEY idx_tasks_requested_at (requested_at),
        CONSTRAINT fk_tasks_user FOREIGN KEY (user_id) REFERENCES users(id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
    """
    CREATE TABLE IF NOT EXISTS results (
        id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        task_id BIGINT UNSIGNED NOT NULL,
        user_id BIGINT UNSIGNED NOT NULL,
        username VARCHAR(64) NOT NULL,
        prompt LONGTEXT NOT NULL,
        image_path VARCHAR(1024) NULL,
        source_url LONGTEXT NULL,
        raw_response_json LONGTEXT NOT NULL,
        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
        model VARCHAR(100) NOT NULL,
        PRIMARY KEY (id),
        KEY idx_results_task_id (task_id),
        KEY idx_results_user_id (user_id),
        KEY idx_results_created_at (created_at),
        KEY idx_results_model (model),
        CONSTRAINT fk_results_task FOREIGN KEY (task_id) REFERENCES tasks(id),
        CONSTRAINT fk_results_user FOREIGN KEY (user_id) REFERENCES users(id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
    """,
)


def initialize_database():
    server_connection = get_connection(include_database=False)
    try:
        cursor = server_connection.cursor()
        cursor.execute(
            f"CREATE DATABASE IF NOT EXISTS `{MYSQL_DATABASE}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        server_connection.commit()
        cursor.close()
    finally:
        server_connection.close()

    connection = get_connection()
    try:
        cursor = connection.cursor()
        for statement in TABLE_STATEMENTS:
            cursor.execute(statement)
        cursor.execute(
            """
            INSERT IGNORE INTO users (username, password_hash, role, api_key_env_var)
            VALUES (%s, %s, %s, %s)
            """,
            (
                DEFAULT_SUPERADMIN_USERNAME,
                generate_password_hash(DEFAULT_SUPERADMIN_PASSWORD),
                ROLE_SUPER_ADMIN,
                DEFAULT_SUPERADMIN_KEY_ENV,
            ),
        )
        connection.commit()
        cursor.close()
    finally:
        connection.close()
