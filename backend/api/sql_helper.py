from requests.utils import quote

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

def esc_db(item):
    return item.replace("'", "\\'")

def sanitize_db_field(db_field):
    special_chars_replace_with_blank = ['"', "\\'", ',']
    special_chars_replace_with_space = ['•']
    sanitized = "REPLACE({}, '{}', '')".format(db_field, special_chars_replace_with_blank.pop(0))
    for s in special_chars_replace_with_blank:
       sanitized = "REPLACE({}, '{}', '')".format(sanitized, s)
    for s in special_chars_replace_with_space:
       sanitized = "REPLACE({}, '{}', ' ')".format(sanitized, s)
    return sanitized

def sanitize_query(query):
    special_chars_replace_with_blank = ['"', "'", ',']
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
