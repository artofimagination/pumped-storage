import psycopg2
from pgcopy import CopyManager
import os


class TimescaleDB():
    DATA_COLUMNS = ['time', 'type', 'data']

    def __init__(self, measurement_types):
        self.buffer = []
        self.measurement_types = measurement_types
        if not self.execute(self.table_exists)[0]:
            print("Init DB")
            self.execute(self.create_measurements_tables)
            self.execute(self.insert_data_types)

    def table_exists(self, _, cursor, __):
        query_exists = """SELECT EXISTS (
                              SELECT FROM
                                  pg_tables
                              WHERE
                                  schemaname = 'public' AND
                                  tablename  = 'measurement_types'
                              );"""
        cursor.execute(query_exists)
        return cursor.fetchone()

    def get_data(self, _, cursor):
        query_get = """SELECT * FROM measurements"""
        cursor.execute(query_get)
        return cursor.fetchall()

    def insert_data_types(self, _, cursor, __):
        for type in self.measurement_types:
            try:
                cursor.execute(
                    "INSERT INTO measurement_types (type, name, description) VALUES (%s, %s, %s);",
                    (type[0], type[1], type[2]))
            except (Exception, psycopg2.Error) as error:
                print(error.pgerror)

    def insert_test_data(self, conn, cursor, _):
        for id in range(0, 2, 1):
            data = (id,)
            # create random data
            test_data = """SELECT generate_series(now() - interval '24 hour', now(), interval '5 minute') AS time,
                              %s as type,
                              random()*100 AS data"""
            cursor.execute(test_data, data)
            values = cursor.fetchall()
            mgr = CopyManager(conn, 'measurements', self.DATA_COLUMNS)
            mgr.copy(values)

    def insert_data(self, _, cursor, data):
        try:
            for key_id, value in data.items():
                cursor.execute(
                    "INSERT INTO measurements (time, type, data) VALUES (now(), %s, %s);",
                    (key_id, value))
        except (Exception, psycopg2.Error) as error:
            print(error.pgerror)

    def create_measurements_tables(self, conn, cursor, _):
        query_create_types_table = """CREATE TABLE measurement_types (
                                            type INTEGER PRIMARY KEY,
                                            name VARCHAR (50),
                                            description VARCHAR (300)
                                            );"""
        query_create_measurements_table = """CREATE TABLE measurements (
                                              time TIMESTAMPTZ NOT NULL,
                                              type INTEGER,
                                              data DOUBLE PRECISION,
                                              FOREIGN KEY (type) REFERENCES measurement_types (type)
                                              );"""
        cursor.execute(query_create_types_table)
        cursor.execute(query_create_measurements_table)
        conn.commit()

    def execute(self, statement, data=None):
        db_name = os.environ['TIMESCALE_DB_NAME']
        user = os.environ['TIMESCALE_DB_USER']
        passwd = os.environ['TIMESCALE_DB_PASSWORD']
        port = os.environ['TIMESCALE_DB_PORT']
        CONNECTION = f"postgres://{user}:{passwd}@172.19.0.1:{port}/{db_name}"
        result = None
        with psycopg2.connect(CONNECTION) as conn:
            cursor = conn.cursor()
            result = statement(conn, cursor, data)
        cursor.close()
        return result
