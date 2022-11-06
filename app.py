# app.py
import multiprocessing
import time
import pickle
from flask import Flask, render_template, request, make_response
import traceback
from flask_assets import Bundle, Environment
import simulator.pkg.src.pkg.main as simCode

app = Flask(__name__)

assets = Environment(app)
css = Bundle("src/main.css", output="dist/main.css")

assets.register("css", css)
css.build()

def simulate(code):
    outL = multiprocessing.Value('d', 0.0)
    process = multiprocessing.Process(target=simCode.testInputDaemon,args=(code,outL))
    process.daemon = True
    process.start()
    
    process.join(50)
    res = outL.value
    if process.is_alive():
        print("Test is hanging!")
        process.terminate()
        print("Terminated!")
        return -1
    return round(res,3)

class Item:
    def __init__(self,name,time):
        self.name=name
        self.time=float(time)
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
    print("table",readPlayers())
    return render_template("leaderboard.html", login_status="", table = readPlayers())


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
        uid = request.cookies.get('userID')

        code = request.form.get("code_")

        result = simulate(simCode.ans)
        #print(result,":D")
        if (result != -1):
            appendPlayer(Item(uid, result)) #log result of the code run
        return render_template("leaderboard.html", run_time=result,  table = readPlayers())
    return render_template("leaderboard.html", table = readPlayers())

@app.route('/base', methods =["GET", "POST"])
def homeFromLeaderboard():
    
    return render_template("base.html", login_status="" )
        
@app.route('/index', methods =["GET", "POST"])
def login():
    if request.method == "POST":
        
        first_name = request.form.get("username")
        
        last_name = request.form.get("pw")

        

        if(first_name=="user"):
            return render_template("leaderboard.html", run_time=1)
        elif(first_name=="test"):
            resp = make_response(render_template("home.html"))
            resp.set_cookie('userID', first_name)
            return resp
        else:
            return render_template("index.html", login_status="Wrong username/password")
        
        # getting input with name = fname in HTML form
        # getting input with name = lname in HTML form
    
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
