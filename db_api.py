############################### SQLITE3 Connections Block Start ###############################

# run select query
def select_query(connection, query, args=(), one=False):
    print(query)
    cursor = connection.cursor()
    cur = cursor.execute(query, args)
    rv = cur.fetchall()
    return (rv[0] if rv else None) if one else rv

# run UID (update, insert, delete) query
def UID_query(connection, query):
    cursor = connection.cursor()
    success = 0
    print(query)
    try:
        cursor.execute(query)
        cursor.close()
        connection.commit()
        success = 1
        print('UID query Success')
    except Exception as e:
        print('UID query Error:', e)
        connection.rollback()

    return success

# run UID (update, insert, delete) query mutiple
def UID_many_query(connection, queries):
    cursor = connection.cursor()
    success = 0
    print(queries)
    try:
        cursor.executescript(queries)
        cursor.close()
        connection.commit()
        success = 1
        print('UID queries Success')
    except Exception as e:
        print('UID queries Error:', e)
        connection.rollback()

    return success

############################### SQLITE3 Connections BLOCK END ###############################