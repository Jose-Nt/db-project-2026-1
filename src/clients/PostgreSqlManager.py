from psycopg2 import sql, extras
import pandas as pd
import psycopg2
import os

class PostgreSqlManager:

    def __init__(
        self
    ) -> None:
        
        self.HOST = os.getenv('HOST')
        self.USER = os.getenv('USER')
        self.PASSWORD = os.getenv('PASSWORD')
        self.PORT = os.getenv('PORT_DB')
        self.DBNAME = os.getenv('DBNAME')

    
    def connect_to_db(
        self
    ) -> psycopg2.extensions.connection:
        """
        Create and return a connection object to PostgreSQL.
        """
        conn = psycopg2.connect(
            host = self.HOST,
            user = self.USER,
            password = self.PASSWORD,
            port = self.PORT,
            dbname = self.DBNAME
        )
        return conn


    def execute_query(
        self,
        query: str,
        params: tuple | None = None
    ) -> pd.DataFrame:
        """
        Executes a SQL query and returns the result as a pandas DataFrame.
        """
        conn = self.connect_to_db()

        try:
            df = pd.read_sql_query(query, conn, params=params)
            return df
        finally:
            conn.close()
            

    def insert_data_into_table(
        self, 
        df: pd.DataFrame, 
        table_name: str
    ) -> None:
        """
        Insert a pandas DataFrame into a PostgreSQL table.
        """
        conn = self.connect_to_db()
        cursor = conn.cursor()

        columns = df.columns.tolist()
        insert_query = sql.SQL("""
            INSERT INTO {table} ({fields}) VALUES ({values})
        """).format(
            table=sql.Identifier(table_name),
            fields=sql.SQL(', ').join(map(sql.Identifier, columns)),
            values=sql.SQL(', ').join(sql.Placeholder() * len(columns))
        )

        data = [
            [None if pd.isna(v) or v == '' else v for v in row]
            for row in df.to_numpy()
        ]
        extras.execute_batch(cursor, insert_query, data, page_size=1000)

        conn.commit()
        cursor.close()
        conn.close()

    
    def delete_rows_by_condition(
        self,
        table_name: str,
        column: str,
        condition: str | int | float
    ):
        """
        Deletes an entire row based on a specific column condition in the PostgreSQL table
        """
        conn = self.connect_to_db()
        cursor = conn.cursor()

        try:
            drop_row_condition_table = f"DELETE FROM {table_name} WHERE {column} = %s"
            cursor.execute(drop_row_condition_table, (condition,))
            print(f'Rows based on the condition "{column} = {condition}" sucessefully excluded.')
        except Exception as error:
            print(f"Failed excluding rows based on the condition. {error}")

        conn.commit()
        cursor.close()
        conn.close()