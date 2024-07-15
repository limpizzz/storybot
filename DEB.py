import sqlite3
import logging
import json

from config import DB_name, Table_name

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="log_file.txt",
    filemode="w",
)


# подключение/создание базы данных
def create_db(database_name: str = DB_name):
    with sqlite3.connect(database_name) as con:
        cur = con.cursor()


# Функция для выполнения любого sql-запроса для изменения данных
def execute_query(sql_query: str, data: tuple = None, db_path: str = DB_name):
    try:
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            if data:
                cursor.execute(sql_query, data)
            else:
                cursor.execute(sql_query)

            connection.commit()

    except:
        logging.debug(f'Информация о пользователе не была изменена.')


# Функция для выполнения любого sql-запроса для получения данных (возвращает значение)
def execute_selection_query(sql_query: str, data: tuple = None, db_path: str = DB_name) -> list:
    try:
        with sqlite3.connect(db_path) as connection:
            cursor = connection.cursor()
            connection.row_factory = sqlite3.Row

            if data:
                cursor.execute(sql_query, data)
            else:
                cursor.execute(sql_query)
            rows = cursor.fetchall()
            return rows

    except:
        logging.debug('Данные не были получены')


# создаем таблицу, если она не создана
def create_table(table_name: str = Table_name):
    sql_query = (
        f"CREATE TABLE IF NOT EXISTS {table_name} "
        f"(id INTEGER PRIMARY KEY, "
        f"user_id INTEGER, "
        f"sessions INTEGER, "
        f"tokens INTEGER, "
        f"genre TEXT, "
        f"hero TEXT, "
        f"setting TEXT,"
        f"additions TEXT,"
        f"messages TEXT);"
    )

    execute_query(sql_query)
    logging.info('Таблица создана')


# проверяем есть ли пользователь в таблице
def is_user_in_db(user_id: int) -> bool:
    sql_query = f"SELECT user_id FROM {Table_name} WHERE user_id = ?;"
    return bool(execute_selection_query(sql_query, (user_id, )))


# добавляем нового пользователя в таблицу
def add_new_user(user_id: int):
    if not is_user_in_db(user_id):
        sql_query = f'INSERT INTO {Table_name} (user_id, sessions, tokens) ' \
                    f'VALUES (?, 0, 1000);'
        execute_query(sql_query, (user_id, ))
        logging.info(f'Пользователь {user_id} добавлен в таблицу')

    else:
        logging.info(f'Пользователь {user_id} уже добавлен в таблицу')


# получаем все данные из таблицы
def get_all_from_table() -> list[tuple[int, int, int, int, str, str, str, str]]:
    sql_query = f'SELECT * FROM {Table_name};'
    res = execute_selection_query(sql_query)
    return res


def update_row(user_id: int, column_name: str, new_value: str | int | None):
    if is_user_in_db(user_id):
        sql_query = (
            f"UPDATE {Table_name} "
            f"SET {column_name} = ? "
            f"WHERE user_id = ?;"
        )

        execute_query(sql_query, (new_value, user_id))

        logging.info(f'Информация о пользователе {user_id} была изменена.')


def get_user_data(user_id: int) -> dict:
    if is_user_in_db(user_id):
        sql_query = (
            f"SELECT * "
            f"FROM {Table_name} "
            f"WHERE user_id = {user_id};"
        )

        row = execute_selection_query(sql_query)[0]
        result = {
            "sessions": row[2],
            "tokens": row[3],
            "genre": row[4],
            "hero": row[5],
            "setting": row[6],
            "additions": row[7],
            "messages": json.loads(row[8]),
        }
        return result