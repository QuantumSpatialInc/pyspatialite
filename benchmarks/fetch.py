import time
import db_row

def yesno(question):
    val = raw_input(question + " ")
    return val.startswith("y") or val.startswith("Y")

use_pysqlite2 = yesno("Use pysqlite 2.0?")
if use_pysqlite2:
    use_custom_types = yesno("Use custom types?")
    use_dictcursor = yesno("Use dict cursor?")
    use_dbrowCursor = yesno("Use db_row cursor?")
else:
    use_tuple = yesno("Use rowclass=tuple?")

if use_pysqlite2:
    from pysqlite2 import dbapi2 as sqlite
else:
    import sqlite

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

if use_pysqlite2:
    class DictCursor(sqlite.Cursor):
        def __init__(self, *args, **kwargs):
            sqlite.Cursor.__init__(self, *args, **kwargs)
            self.row_factory = lambda row: dict_factory(self, row)

    class DbRowCursor(sqlite.Cursor):
        def execute(self, *args, **kwargs):
            sqlite.Cursor.execute(self, *args, **kwargs)
            if self.description:
                self.row_factory = db_row.IMetaRow(self.description)

def create_db():
    if sqlite.version_info > (2, 0):
        if use_custom_types:
            con = sqlite.connect(":memory:", detect_types=sqlite.PARSE_DECLTYPES|sqlite.PARSE_COLNAMES)
            con.converters["text"] = lambda x: "<%s>" % x
        else:
            con = sqlite.connect(":memory:")
        if use_dbrowCursor:
            cur = con.cursor(factory=DbRowCursor)
        elif use_dictcursor:
            cur = con.cursor(factory=DictCursor)
        else:
            cur = con.cursor()
    else:
        if use_tuple:
            con = sqlite.connect(":memory:")
            con.rowclass = tuple
            cur = con.cursor()
        else:
            con = sqlite.connect(":memory:")
            cur = con.cursor()
    cur.execute("""
        create table test(v text, f float, i integer)
        """)
    return (con, cur)

def test():
    row = ("sdfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffasfd", 3.14, 42)
    l = []
    for i in range(1000):
        l.append(row)

    con, cur = create_db()

    if sqlite.version_info > (2, 0):
        sql = "insert into test(v, f, i) values (?, ?, ?)"
    else:
        sql = "insert into test(v, f, i) values (%s, %s, %s)"

    for i in range(50):
        cur.executemany(sql, l)

    cur.execute("select count(*) as cnt from test")

    starttime = time.time()
    for i in range(50):
        cur.execute("select v, f, i from test")
        l = cur.fetchall()
    endtime = time.time()

    print "elapsed:", endtime - starttime

if __name__ == "__main__":
    test()

