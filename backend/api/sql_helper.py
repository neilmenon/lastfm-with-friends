import json
from requests.utils import quote
import mariadb
from . import api_logger as logger
from flask import abort, make_response, jsonify, g
from . import config

cfg = config.config

def insert_into(table, data):
    columns = ', '.join("`" + str(x) + "`" for x in data.keys())
    values = ', '.join("'" + str(x) + "'" for x in data.values())
    sql = "INSERT INTO %s ( %s ) SELECT %s" % (table, columns, values)
    return sql

def insert_into_where_not_exists(table, data, unique):
    columns = ', '.join("`" + str(x) + "`" for x in data.keys())
    values = ', '.join("'" + str(x) + "'" for x in data.values())
    sql = "INSERT INTO %s ( %s ) SELECT %s" % (table, columns, values)
    sql += " FROM DUAL WHERE NOT EXISTS (SELECT * FROM "+table+" WHERE " + unique + " = '"+str(data[unique])+"');"
    return sql

def insert_into_where_not_exists_2(table, data, unique1, unique2):
    columns = ', '.join("`" + str(x) + "`" for x in data.keys())
    values = ', '.join("'" + str(x) + "'" for x in data.values())
    sql = "INSERT INTO %s ( %s ) SELECT %s" % (table, columns, values)
    sql += " FROM DUAL WHERE NOT EXISTS (SELECT * FROM "+table+" WHERE " + unique1 + " = '"+str(data[unique1])+"' AND " + unique2 + " = '"+str(data[unique2])+"');"
    return sql

def replace_into(table, data):
    columns = ', '.join("`" + str(x) + "`" for x in data.keys())
    values = ', '.join("'" + str(x) + "'" for x in data.values())
    sql = "REPLACE INTO %s ( %s ) VALUES ( %s )" % (table, columns, values)
    return sql

def esc_db(item: str):
    item_1 =  item.replace("'", "\\'") if "\\'" not in item else item.replace("\\", "").replace("'", "\\'")
    if item_1:
        if (len(item_1) == 1 and item_1[-1] == "\\"):
            item_1 = "\\"
        elif (len(item_1) >= 2 and item_1[-1] == "\\" and item_1[-2] != "\\"):
            item_1 = item_1 + "\\"
    return item_1

def sanitize_db_field(db_field):
    special_chars_replace_with_blank = ['"', "\\'"]
    special_chars_replace_with_space = ['•']
    sanitized = "REPLACE({}, '{}', '')".format(db_field, special_chars_replace_with_blank.pop(0))
    for s in special_chars_replace_with_blank:
       sanitized = "REPLACE({}, '{}', '')".format(sanitized, s)
    for s in special_chars_replace_with_space:
       sanitized = "REPLACE({}, '{}', ' ')".format(sanitized, s)
    return sanitized

def sanitize_query(query):
    special_chars_replace_with_blank = ['"', "'"]
    special_chars_replace_with_space = ['•']
    for s in special_chars_replace_with_blank:
        query = query.replace(s, '')
    for s in special_chars_replace_with_space:
        query = query.replace(s, ' ')
    return query

def format_lastfm_string(url_string):
    safe = '():'
    if "+" not in url_string:
        url_string = url_string.replace(" ", "+")
        safe += "+"
    return quote(url_string, safe=safe)

def get_db():
    if 'db' not in g:
        g.db = mariadb.connect(**(cfg['sql']))

    return g.db

def execute_db(sql, commit=False, tz=False, log=False, pass_on_error=False):
    mdb = get_db()
    cursor = mdb.cursor(dictionary=True)
    if tz:
        cursor.execute("SET time_zone='+00:00';")

    try:
        if log or cfg['sql_logging']:
            logger.debug("Executing SQL: {}".format(sql))
        cursor.execute(sql)
        records = [] if commit else list(cursor)
        if commit:
                mdb.commit()
    except mariadb.Error as e:
            logger.error("{} A database error occured: {}".format("[PASS]" if pass_on_error else "[FATAL]", e))
            logger.error("\tSQL: {}".format(sql))
            records = []
            if not pass_on_error:
                abort(make_response(jsonify(error="A database error occured: {}".format(e)), 500))

    return records

# built for personal stats 
def stringify_keys_in_dict(d: dict):
    for k in d.keys():
        if type(d[k]) is dict or type(d[k]) is list:
            d[k] = json.dumps(d[k], ensure_ascii=False).replace("'", "\\'")

    return d

def escape_keys_in_dict(d: dict):
    for k in d.keys():
        if type(d[k]) is str:
            d[k] = d[k].replace("'", "\'")

    return d