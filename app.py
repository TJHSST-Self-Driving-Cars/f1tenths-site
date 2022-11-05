# app.py
import multiprocessing
import time
import pickle
from flask import Flask, render_template, request
import traceback
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
    def __init__(self,name,time):
        self.name=name
        self.time=int(time)
        self.rank=0
    def __repr__(self):
        return self.name+" "+str(self.time)
    def __lt__(self,other):
        return self.time < other.time


items = [         
         Item("Vrishak","6"),
         Item('Krishnan','9'),
         Item('Me','11')]

def readPlayers():
    try:
        file = open('members.pickle', 'rb')
        o = pickle.load(file)
        
        return o
    except FileNotFoundError:
        pass
    except EOFError:
        pass
    return []

def writePlayers(items):
    items.sort()
    for i in range(len(items)):
        items[i].rank=i+1
    file = open('members.pickle', 'wb+') 
    pickle.dump(items, file)
    file.close()

def appendPlayer(item):
    l = readPlayers()
    #print("L\n\n",l,"\n\n")
    inTab = False
    for i in range(len(l)):
        if l[i].name==item.name:
            inTab = True
            l[i].time=min(l[i].time,item.time)
    if not inTab:    
        l.append(item)
    writePlayers(l)


@app.route('/leaderboard', methods =["GET", "POST"])
def leaderboard():

    if request.method == "POST":
        return render_template("leaderboard.html", isLogged="", table = readPlayers())

@app.route('/leaderboard2', methods =["GET", "POST"])
def leaderboard2():

    if request.method == "POST":
        return render_template("leaderboard2.html", isLogged="", table = readPlayers())


@app.route("/")
def homepage():
    return render_template("index.html", login_status="")


@app.route('/yay', methods =["GET", "POST"])
def codesubmit():
    if request.method == "POST":
        code = request.form.get("code_")
        try:
            result = simCode.testCode(code)
            return render_template("yay.html", run_time=result)

        except Exception as e:
            
            tb = traceback.format_exc()
            return render_template("error.html", error_=tb)

@app.route('/base', methods =["GET", "POST"])
def homeFromLeaderboard():
    
    return render_template("base.html", login_status="" )
        
@app.route('/index', methods =["GET", "POST"])
def login():
    if request.method == "POST":
        
        first_name = request.form.get("username")
        
        last_name = request.form.get("pw")
        if(first_name=="user"):
            
            result = f("Ad") #simCode.testCode()
            if (result > 0): #if successful
                appendPlayer(Item(first_name,result))
            return render_template("yay.html", run_time=str(result))
        elif(first_name=="test"):
            return render_template("home.html")
        # getting input with name = fname in HTML form
        # getting input with name = lname in HTML form
        else:
            return render_template("index.html", login_status="Wrong username/password")
@app.route('/codesubmit', methods =["GET", "POST"])
def toCode():
    
    if request.method == "POST":
        return render_template("codesubmit.html")
    
    
@app.route('/home', methods =["GET", "POST"])
def back2home():
    
    if request.method == "POST":
        return render_template("home.html")



if __name__ == "__main__":
    app.run(debug=True)
