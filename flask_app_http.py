from http import HTTPStatus
from typing import Optional

from flask import Flask, Response, redirect, request, url_for
from gevent.pywsgi import WSGIServer

app = Flask(__name__)

@app.before_request
def force_https():
    if not request.is_secure:
        return redirect(request.url.replace('http://', 'https://'))

@app.route("/")
def index():
    return 'hello'


if __name__ == '__main__':
    app.config["SECRET_KEY"] = '_x9^5#av)@-7b^m^4i7tg2=d$0@qc9=$74kbe8os$8^q4um27='
    http_server = WSGIServer(('0.0.0.0', 80), app)
    http_server.serve_forever()