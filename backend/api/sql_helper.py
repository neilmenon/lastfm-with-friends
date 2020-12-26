def insert_into_where_not_exists(table, data, unique):
    columns = ', '.join("`" + str(x).replace('/', '_') + "`" for x in data.keys())
    values = ', '.join("'" + str(x).replace('/', '_') + "'" for x in data.values())
    sql = "INSERT INTO %s ( %s ) SELECT %s" % (table, columns, values)
    sql += " FROM DUAL WHERE NOT EXISTS (SELECT * FROM "+table+" WHERE " + unique + " = \""+data[unique]+"\");"
    return sql