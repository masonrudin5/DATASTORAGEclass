# Configuration settings for database connection!

dbhost = 'db.cs.usna.edu'
dbuser = 'm285640'
dbpass = 'm285640'
dbname = 'm285640'

import MySQLdb

'''
Our connection class is used to initialize a connection to MySQL and
to support basic queries of the database.
'''
class connection:
    '''
    Initialize the connection and set basic connection information
    such as autocommiting data and setting the format of returned results.
    '''
    def __init__(self, dbuser, dbpass, dbhost, dbname):
        self.db = MySQLdb.connect(dbhost, dbuser, dbpass, dbname)
        self.db.autocommit(True)
        self.db.query("set character_set_client='utf8'")
        self.db.query("set character_set_results='utf8'")
        self.db.query("set collation_connection='utf8_general_ci'")

    '''
    Submit a SQL statement to the database and return the results and/or
    Errors and Warnings.
    '''
    def query(self, sql, *data):
        cursor = self.db.cursor()
        error = ""
        try:
            if data and data != []:         # If prepared data was sent to function use it
                cursor.execute(sql, data[0])# Execute a prepared statement
            else:
                cursor.execute(sql)         # Execute a normal SQL statement
        except MySQLdb.Error as e:          # Return any errors from MySQLdb
            error = str(e)

                  # Retrieve any warnings
        insert_id = cursor.lastrowid        # Get the last row id (from any inserts)
        column_info = cursor.description    # Retrieve column names and info

        try:
            data = cursor.fetchall()        # Retrieve all of the rows
        except:
            data = []

        cursor.close()                      # Close the cursor

        return column_info, data, insert_id, error

    '''
    Submit a SQL statement to the database and
    return the results as a pandas dataframe with any critical errors.
    '''
    def querydf(self, sql, *data):
        import pandas as pd
        error = ""
        try:
            if data and data != []:         # If prepared data was sent to function use it
                df = pd.read_sql_query(sql, self.db, params=data[0])
            else:
                df = pd.read_sql_query(sql, self.db)
        except MySQLdb.Error as e:          # Return any errors from MySQLdb
            error = str(e)
            df = None

        return df, error

    '''
    Close our connection to the database
    '''
    def close(self):
        self.db.close()

db = connection(dbuser, dbpass, dbhost, dbname)
