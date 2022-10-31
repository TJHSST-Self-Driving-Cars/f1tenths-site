# app.py

from flask import Flask, render_template, request
from flask_assets import Bundle, Environment
import simulator.pkg.src.pkg.main as simCode

app = Flask(__name__)

assets = Environment(app)
css = Bundle("src/main.css", output="dist/main.css")

assets.register("css", css)
css.build()


@app.route("/")
def homepage():
    return render_template("index.html", login_status="")



@app.route('/', methods =["GET", "POST"])
def login():
    if request.method == "POST":
        
        first_name = request.form.get("username")
        
        last_name = request.form.get("pw")
        if(first_name=="user"):
            
            result = simCode.testCode()
            return render_template("yay.html", run_time=str(result))
        # getting input with name = fname in HTML form
        # getting input with name = lname in HTML form
    return render_template("index.html", login_status="Wrong username/password")


if __name__ == "__main__":
    app.run(debug=True)