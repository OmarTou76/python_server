from flaskext.mysql import MySQL


class Database:
    def __init__(self, app):
        self.mysql = MySQL()
        self._addConfig(app)
        self.mysql.init_app(app)
        self.conn = self.mysql.connect()

    def _addConfig(self, app):
        app.config["MYSQL_DATABASE_USER"] = "root"
        app.config["MYSQL_DATABASE_PASSWORD"] = "123456789"
        app.config["MYSQL_DATABASE_DB"] = "bicycle_shop"
        app.config["MYSQL_DATABASE_HOST"] = "localhost"

    def query(self, sql):
        cursor = self.conn.cursor()
        cursor.execute(sql)
        keys = [x[0] for x in cursor.description]
        values = cursor.fetchall()
        rows = []
        for value in values:
            rows.append(dict(zip(keys, value)))
        return rows


class Queries:
    def findOne(db, name):
        q = "SELECT * FROM bike WHERE name = " + '"{}"'.format(name)
        data = db.query(q)
        return data

    def allItems(db):
        return db.query("SELECT * FROM bike")

    def withCondition(condition, db):
        dictQuery = condition.to_dict(flat=False)
        checkSelection = allSelected(dictQuery)
        sqlQuery = sqlConverter(checkSelection)
        query = db.query(sqlQuery)
        return query


def allSelected(req):
    maxItems = {"type": 2, "practice": 6, "brand": 2}
    temp = dict(req)
    for v in list(req):
        if v in maxItems and len(req[v]) == maxItems[v]:
            del temp[v]

    return temp


def sqlConverter(condition):
    sentenceArr = []
    for key, value in condition.items():
        if key == "practice":
            temp = []
            length = len(value) - 1
            for e in value:
                sentence = key + " = " '"{}"'.format(e)
                if e != value[length]:
                    sentence += " OR "
                temp.append(sentence)
            if len(temp) == 1:
                sentenceArr.append("".join(temp))
            else:
                sentenceArr.append("(" + "".join(temp) + ")")
            continue
        if key == "price":
            sentenceArr.append(key + " < " + value[0])
            continue
        if key != "name" and key != "limit":
            sentenceArr.append(key + " = " + '"{}"'.format(value[0]))
    sentenceQuery = " AND ".join(sentenceArr)
    finalSentence = "SELECT * FROM bike "
    if not sentenceQuery:
        return finalSentence
    if "limit" in condition.keys():
        if sentenceQuery:
            finalSentence += (
                "WHERE " + sentenceQuery + " LIMIT " + condition["limit"][0]
            )
        else:
            finalSentence += "LIMIT " + condition["limit"][0]
        return finalSentence

    return finalSentence + "WHERE " + sentenceQuery
