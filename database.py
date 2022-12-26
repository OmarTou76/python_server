from flaskext.mysql import MySQL
import datetime


class Database:
    def __init__(self, app):
        self.app = app
        self.mysql = MySQL()
        self._addConfig()
        self.mysql.init_app(self.app)
        self.conn = self.mysql.connect()

    def _addConfig(self):
        self.app.config["MYSQL_DATABASE_USER"] = "root"
        self.app.config["MYSQL_DATABASE_PASSWORD"] = "123456789"
        self.app.config["MYSQL_DATABASE_DB"] = "bicycle_shop"
        self.app.config["MYSQL_DATABASE_HOST"] = "localhost"

    def query(self, sql):
        cursor = self.conn.cursor()
        cursor.execute(sql)
        keys = [x[0] for x in cursor.description]
        values = cursor.fetchall()
        rows = []
        for row in values:
            for i, value in enumerate(row):
                if isinstance(value, datetime.datetime):
                    new_value = value.strftime("%Y-%m-%d %H:%M:%S")
                    row = row[:i] + (new_value,) + row[i + 1 :]
            rows.append(dict(zip(keys, row)))
        self.conn.commit()
        return rows

    def update_user(self, req):
        cursor = self.conn.cursor()
        cursor.execute(req)
        self.conn.commit
        cursor.close()

    def add_user(self, user):
        try:
            cursor = self.conn.cursor()
            cursor.execute(user)
            result = cursor.fetchone()
            self.conn.commit()
            if result is None:
                return [None, "Registration done!", True]
            else:
                return ["An error occurred while registering", False]
        except Exception as e:
            err = e.args
            return [err[0], err[1], False]

    def add_order(self, client, order):
        cursor = self.conn.cursor()
        order_q = "INSERT INTO orders (client_id) VALUES ({})".format(int(client))
        cursor.execute(order_q)
        self.conn.commit()
        order_id = cursor.lastrowid
        item_q = "INSERT INTO order_items (order_id, name_item, size, quantity, price) VALUES ({}, '{}', '{}', {}, {})"
        for item in order:
            # pb with quote ('')
            size = item["size"].replace("'", "\\'")
            cursor.execute(
                item_q.format(
                    int(order_id),
                    item["name"],
                    size,
                    int(item["quantity"]),
                    int(item["price"]),
                )
            )
        self.conn.commit()
        cursor.close()


class Queries:
    def findOne(db, name):
        q = "SELECT * FROM bike WHERE name = '{}'".format(name)
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

    def create_user(db, data):
        q = "INSERT INTO users_profil (first_name, last_name, password, email, phone_number, city, country, create_time, last_connection) VALUES ('{}','{}','{}','{}','{}','{}','{}', NOW(), NOW())"
        user_query = q.format(
            data["first_name"],
            data["last_name"].upper(),
            data["password"],
            data["email"],
            data["phone"],
            data["city"].upper(),
            data["country"].upper(),
        )
        userStatus = db.add_user(user_query)

        # if user is added
        if userStatus[2] == True:
            user = db.query(
                "SELECT * FROM users_profil WHERE email = '{}'".format(data["email"])
            )
            return {
                "email": data["email"],
                "user": user[0],
                "error_code": userStatus[0],
                "error": userStatus[1],
                "continue": userStatus[2],
            }

        return {
            "email": data["email"],
            "error_code": userStatus[0],
            "error": userStatus[1],
            "continue": userStatus[2],
        }

    def login(db, data):
        q = "SELECT * FROM users_profil WHERE email = '{}'".format(data["email"])
        db.update_user(
            "UPDATE users_profil SET last_connection = NOW() WHERE email = '{}'".format(
                data["email"]
            )
        )

        user_data = db.query(q)

        # check if email exist
        if len(user_data) == 0:
            return {
                "continue": False,
                "error_message": "Invalid email",
                "error_field": "email",
            }
        if data["password"] != user_data[0]["password"]:
            return {
                "continue": False,
                "error_message": "Invalid password",
                "error_field": "password",
            }
        return {"continue": True, "data": user_data[0]}


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
