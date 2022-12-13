from flask import Flask, request, send_file, Response
from flask_cors import CORS, cross_origin
from database import Database, Queries
import os
import json

app = Flask(__name__)
CORS(app)
db = Database(app)


@app.route("/")
@cross_origin()
def index():
    name = request.args.get("name")
    if name == "ALL":
        if len(request.args) == 1:
            data = Queries.allItems(db)
        else:
            data = Queries.withCondition(request.args, db)
    else:
        data = Queries.findOne(db, name)
    return Response(json.dumps(data), mimetype="application/json")


@app.route("/image")
def image():
    name = request.args.get("name").replace(" ", "_") + ".png"
    path = "static/images/"
    if not os.path.exists(path + name):
        name = "error.png"
    return send_file(path + name, mimetype="image/png")


if __name__ == "__main__":
    app.run(host="localhost", port=4000, debug=True)
