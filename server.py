from flask import Flask, request, send_file, Response
from flask_cors import CORS, cross_origin
from database import Database, Queries
from flask_restful import Resource, Api
import json
import os
from newsletter import email

app = Flask(__name__)
CORS(app)
api = Api(app)
db = Database(app)


class Bikes(Resource):
    def get(self):
        name = request.args.get("name")
        if name == "ALL":
            if len(request.args) == 1:
                data = Queries.allItems(db)
            else:
                data = Queries.withCondition(request.args, db)
        else:
            data = Queries.findOne(db, name)
        return data


class User(Resource):
    def get(self):
        email = request.args.get("email")
        return db.query("SELECT * FROM users_profil WHERE email = '{}'".format(email))


class Image(Resource):
    def get(self):
        name = request.args.get("name").replace(" ", "_") + ".png"
        path = "static/images/"
        if not os.path.exists(path + name):
            name = "error.png"
        return send_file(path + name, mimetype="image/png")


class Video(Resource):
    def get(self):
        name = "video2.mp4"
        path = "static/videos/"
        return send_file(path + name, mimetype="video/mp4")


class Sign_up(Resource):
    def post(self):
        data = request.get_json()["values"]
        user_response = Queries.create_user(db, data)
        return user_response


class Sign_in(Resource):
    def post(self):
        data = request.get_json()["values"]
        check = Queries.login(db, data)
        return check


class Newsletter(Resource):
    def post(self):
        data = request.get_json()
        response = {}
        response["email"] = data["email"]
        if data["email"] in email:
            response["message"] = "{} is already to the newsletter.".format(
                data["email"]
            )
            response["color"] = "white"
            response["background"] = "#F49D1A"
        else:
            with open("newsletter.py", "r+") as f:
                contenu = f.read()
                contenu = contenu.replace("]", ",'" + str(data["email"]) + "']")
                f.seek(0)
                f.write(contenu)
            response["message"] = "{} is subscribed to the newsletter.".format(
                data["email"]
            )
            response["color"] = "white"
            response["background"] = "green"
        return response


class Order(Resource):
    def post(self):
        data = request.get_json()
        Database.add_order(db, data["client"], data["items"])
        return {"continue": True}

    def get(self):
        user_id = request.args["id"]
        rows = db.query(
            "SELECT * FROM orders AS o JOIN order_items AS oi ON o.id = oi.order_id WHERE o.client_id = {}".format(
                user_id
            )
        )
        rows_order = {}
        for order in rows:
            if not str(order["order_id"]) in rows_order:
                rows_order[str(order["order_id"])] = []
            rows_order[str(order["order_id"])].append(order)
        return rows_order


api.add_resource(Bikes, "/")
api.add_resource(Image, "/image")
api.add_resource(Video, "/video")
api.add_resource(Sign_in, "/login")
api.add_resource(Sign_up, "/create_account")
api.add_resource(Newsletter, "/newsletter")
api.add_resource(User, "/user")
api.add_resource(Order, "/order")

if __name__ == "__main__":
    app.run(debug=True, port=4000)
