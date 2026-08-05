import mysql.connector

from ..config import (
    MYSQL_CHARSET,
    MYSQL_DATABASE,
    MYSQL_HOST,
    MYSQL_PASSWORD,
    MYSQL_PORT,
    MYSQL_USER,
)


def get_connection(include_database=True):
    options = {
        "host": MYSQL_HOST,
        "port": MYSQL_PORT,
        "user": MYSQL_USER,
        "password": MYSQL_PASSWORD,
        "charset": MYSQL_CHARSET,
        "autocommit": False,
    }
    if include_database:
        options["database"] = MYSQL_DATABASE
    return mysql.connector.connect(**options)

