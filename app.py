# app.py
import multiprocessing
import time
import pickle
from flask import Flask, render_template, request

from flask_assets import Bundle, Environment
import simulator.pkg.src.pkg.main as simCode

app = Flask(__name__)

assets = Environment(app)
css = Bundle("src/main.css", output="dist/main.css")

assets.register("css", css)
css.build()



def f(ads):
    return 10

def simulate(code):
    process = multiprocessing.Process(target=f,args=(code,))
    process.daemon = True
    process.start()
    process.join(5)
    if process.is_alive():
        print("Test is hanging!")
        process.terminate()
        print("Terminated!")
        return process.get()
    return process.get()

class Item:
    def __init__(self,name,rank,time):
        self.name=name
        self.rank=int(rank)
        self.time=int(time)
    def __lt__(self,other):
        return self.time < other.time


items = [         
         Item("Vrishak", '2',"6"),
         Item('Krishnan', '3','9'),
         Item('Me', '1','5')]

def readPlayers():
    file = open('members.pickle', 'rb')
    object = pickle.load(file)
    object.sort()
    for i in range(len(object)):
        object[i].rank=i+1
    return object

def writePlayers(items):
    file = open('members.pickle', 'wb+') 
    pickle.dump(items, file)
    file.close()

@app.route("/leaderboard")
def leaderboard():
    return render_template("leaderboard.html", login_status="", table = readPlayers())



@app.route("/")
def homepage():
    return render_template("index.html", login_status="")

@app.route('/', methods =["GET", "POST"])
def login():
    if request.method == "POST":
        
        first_name = request.form.get("username")
        
        last_name = request.form.get("pw")
        if(first_name=="user"):
            
            result = f("Ad") #simCode.testCode()
            return render_template("yay.html", run_time=str(result))
        # getting input with name = fname in HTML form
        # getting input with name = lname in HTML form
    return render_template("index.html", login_status="Wrong username/password")


if __name__ == "__main__":
    app.run(debug=True)
