import mariadb
import datetime
import requests
import config
import sql_helper

cfg = config.config

'''
    returns True if session key is valid and matches the user
    returns False if the above are false
'''
def is_authenticated(username, session_key):
    mdb = mariadb.connect(**(cfg['sql']))
    cursor = mdb.cursor(dictionary=True)
    sql = 'SELECT * FROM sessions WHERE session_key = "'+session_key+'";'
    print(sql)
    cursor.execute(sql)
    result = list(cursor)
    if len(result) > 0:
        session = result[0]
        if session['username'] != username:
            return "User does not match session key."
        sql = "UPDATE `sessions` SET `last_used` = '"+str(datetime.datetime.now())+"' WHERE `sessions`.`session_key` = '"+session_key+"'"
        cursor.execute(sql)
        mdb.commit()
        return session
    else: # session key not found in database, check if the provided one is valid
        return "No key found."
    return True

print(is_authenticated("neilmenon", "123"))