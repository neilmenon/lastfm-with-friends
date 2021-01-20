def insert_into(table, data):
    columns = ', '.join("`" + str(x) + "`" for x in data.keys())
    values = ', '.join("'" + str(x) + "'" for x in data.values())
    sql = "INSERT INTO %s ( %s ) SELECT %s" % (table, columns, values)
    return sql

def insert_into_where_not_exists(table, data, unique):
    columns = ', '.join("`" + str(x) + "`" for x in data.keys())
    values = ', '.join("'" + str(x) + "'" for x in data.values())
    sql = "INSERT INTO %s ( %s ) SELECT %s" % (table, columns, values)
    sql += " FROM DUAL WHERE NOT EXISTS (SELECT * FROM "+table+" WHERE " + unique + " = \""+data[unique]+"\");"
    return sql

def replace_into(table, data):
    columns = ', '.join("`" + str(x) + "`" for x in data.keys())
    values = ', '.join("'" + str(x) + "'" for x in data.values())
    sql = "REPLACE INTO %s ( %s ) VALUES ( %s )" % (table, columns, values)
    return sql

def esc_db(item):
    return item.replace("'", "\\'")