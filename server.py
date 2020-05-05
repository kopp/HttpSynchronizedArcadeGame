import pprint
from flask import Flask, request, jsonify
app = Flask(__name__)


data = {}


@app.route('/')
def hello_world():
    return 'Hello, World!'


@app.route("/update", methods=["POST"])
def receive_update():
    new_data = request.get_json()
    if new_data is not None:
        global data
        data.update(new_data)
    return jsonify(data)

CLEAR_DATA_PATH = "/clear_data"
@app.route(CLEAR_DATA_PATH, methods=["GET", "POST"])
def clear_data():
    if request.method == "GET":
        return f"""
        <html>
            <body>
                <h1>Clear data?</h1>
                <form action="{CLEAR_DATA_PATH}" method="post">
                    <button type="submit" name="clear" value="1">Clear Data</button>
                </form>
            </body>
        </html>
        """
    elif request.method == "POST":
        global data
        data = {}
        return "Data cleared"

@app.route("/display_data")
def display_data():
    return f"""
    <html>
        <body>
            <h1>Data:</h1>
            <pre>
{pprint.pformat(data)}
            </pre>
        </body>
    </html>
    """


if __name__ == "__main__":
    app.run(debug=True)
