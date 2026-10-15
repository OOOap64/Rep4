import os
from collections import Counter
from datetime import timedelta
import sqlite3 as sql
import hashlib
from flask import Flask, request, url_for, render_template, redirect, jsonify


from flask_jwt_extended import  JWTManager, create_access_token,  create_refresh_token,jwt_required, get_jwt_identity, set_access_cookies, set_refresh_cookies

import jwt
from dotenv import load_dotenv

load_dotenv()

app=Flask(__name__, static_folder="static")

app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY","super-secret")
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=15)
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
app.config["JWT_TOKEN_LOCATION"] = ["cookies"]
app.config["JWT_COOKIE_CSRF_PROTECT"] = False
app.config["JWT_COOKIE_SECURE"] = False

jwt = JWTManager(app)

def conn():def conn():
    con=sql.connect("sqlite.db")
    cur=con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS User (
            id       INTEGER PRIMARY KEY,
            name     TEXT    NOT NULL UNIQUE,
            password TEXT    NOT NULL,
            grp      TEXT,
            post     TEXT
        );
    """)
    con.commit()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS Task (
            id   INTEGER PRIMARY KEY,
            task TEXT,
            u_id INTEGER,
            type TEXT
        );
    """)
    con.commit()
    return  con, cur


@jwt_required()
def is_teamlead():
    con, cur= conn()
    nm=get_jwt_identity()
    cur.execute(f"SELECT post FROM User WHERE name='{nm}'")
    aa=cur.fetchone()
    if aa[0]!="TeamLead":
        cur.close()
        con.close()
        return redirect(url_for("ui"))
    cur.close()
    con.close()

@app.route("/home")
@jwt_required()
def ui():
    con, cur=conn()
    currn_us=get_jwt_identity()
    cur.execute(f"SELECT * FROM User WHERE name='{currn_us}';")
    us=cur.fetchone()
    cur.execute(f"SELECT * FROM User WHERE grp='{us[3]}';")
    uss=cur.fetchall()

    cur.execute(f"SELECT *, us.id FROM Task join User us on us.name=Task.executer WHERE Task.type=0 and us.grp='{us[3]}';")
    tsk1=cur.fetchall()
    cur.execute(f"SELECT *, us.id FROM Task join User us on us.name=Task.executer WHERE Task.type=1 and us.grp='{us[3]}';")
    tsk2=cur.fetchall()
    cur.execute(f"SELECT *, us.id FROM Task join User us on us.name=Task.executer WHERE Task.type=2 and us.grp='{us[3]}';")
    tsk3=cur.fetchall()
    print(tsk1)

    print(us)
    cur.close()
    con.close()

    return render_template("UI.html", 
                            nm=us,
                            us=uss,
                           tsk=tsk1,
                           tsk2= tsk2, 
                           tsk3= tsk3)
        


@app.route("/", methods=["POST", "GET"])
def reg_post():
    err=""
    if request.method=="POST":
        con, cur=conn()
        # hss=[p[-1] for p in uss]
        cur.execute("SELECT * from User;")
        uss=cur.fetchall()
        pws=[p[2] for p in uss]
        nms=[p[1] for p in uss]
        nm=request.form["name"]
        pw=request.form["password"]
        pw=pw.encode("utf-8")
        hsh_ob=hashlib.sha256()
        hsh_ob.update(pw)
        pw=hsh_ob.hexdigest()
        ps=request.form["post"]
        gp=request.form["grp"]
        if nm not in nms:
            cur.execute(f"SELECT post from User WHERE grp='{gp}';")
            us_gr=cur.fetchall()
            cur.execute(f"SELECT COUNT(*) FROM User WHERE post='TeamLead' AND grp='{gp}'")
            tem=cur.fetchone()
            if len(nm)>4 and len(pw)>4 and nm not in nms:
                if len(tem)<=1:  
                    cur.execute(f"""INSERT INTO User VALUES({len(uss)+1}, '{nm}', '{ps}', '{gp}', '{pw}' );""" )
                    con.commit()
                    cur.close()
                    con.close()
                    access_tkn=create_access_token(identity=nm)
                    refresh_access_tkn=create_refresh_token(identity=nm)
                    response = redirect(url_for('ui'))
                    set_access_cookies(response, access_tkn)
                    set_refresh_cookies(response, refresh_access_tkn)
                    return response
            
            err=f"Wrong print"
            return render_template("index.html", err=err)
        else:
            cur.execute(f"SELECT * FROM User WHERE name='{nm}'")
            dt=cur.fetchone()
            
            if dt[1]==nm and pw==dt[4] and ps==dt[2] and gp==dt[3]:
              
              access_tkn=create_access_token(identity=nm)
              refresh_access_tkn=create_refresh_token(identity=nm)
              response = redirect(url_for('ui'))
              set_access_cookies(response, access_tkn)
              set_refresh_cookies(response, refresh_access_tkn)
              return response
        err=f"Wrong print"
        cur.close()
        con.close()    
    # yield jsonify({"msg":"Nothing"})
    return render_template("index.html", err=err)

# @app.route("/add_task", methods=["GET"])
# @jwt_required()
# def get_addtsk():
#     con, cur=conn()
#     us=get_jwt_identity()
#     cur.execute(f"SELECT * FROM User WHERE name='{us}'")
#     uss=cur.fetchone()
#     cur.close()
#     con.close() 
#     return render_template("add_task.html", uss=uss)  
  
@app.route("/add_task", methods=["POST", "GET"])
def post_addtsk():
    is_teamlead()
    con, cur=conn()
    us=get_jwt_identity()
    cur.execute(f"SELECT * FROM User WHERE grp = (SELECT grp FROM User WHERE name='{us}');")
    uss=cur.fetchall()
    if request.method=="POST":
        
        ex=request.form["executer"]
        tk=request.form["task"]
        cur.execute(f"SELECT * FROM User WHERE name='{ex}'")
        exs=cur.fetchone()
        cur.execute(f"SELECT id FROM Task")
        tsk=cur.fetchall()

        print(exs)
        cur.execute(f"INSERT INTO Task(id, task, executer, type) VALUES( {len(tsk)}, '{tk}', '{ex}', 0 );")
        con.commit()  
        cur.close()
        con.close() 
        return redirect(url_for('ui'))
    return render_template("add_task.html", uss=uss)   

@app.route("/transform1/<int:id>")
def tran1(id):
    is_teamlead()
    con, cur=conn()
    cur.execute(f"UPDATE Task  SET type=type+1 WHERE id={id};")
    con.commit()
    cur.close()
    con.close()
    return redirect(url_for("ui"))

@app.route("/edit/<int:id>", methods=["POST", "GET"])
@jwt_required()
def edit(id):
    is_teamlead()
    nm=get_jwt_identity()
    con, cur=conn()
    cur.execute(f"SELECT grp FROM User where name='{nm}';")
    g=cur.fetchone()
    cur.execute(f"SELECT * FROM User where grp='{g[0]}'; ")
    uss=cur.fetchall()
    if request.method=="POST":
        tsk=request.form["task"]
        e=request.form["executer"]
        con, cur=conn()
        cur.execute(f"UPDATE Task SET task='{tsk}', executer='{e}' WHERE id={id} ;")
        con.commit()
        cur.close()
        con.close()
        return redirect(url_for("ui"))
    return render_template("add_task.html", uss=uss)

@app.route("/delete/<int:id>")
def delete(id):
    is_teamlead()
    con, cur=conn()
    cur.execute(f"DELETE FROM Task WHERE id={id} ;")
    con.commit()
    cur.close()
    con.close()
    return redirect(url_for("ui"))

if __name__=="__main__":
    app.run(debug=True, port="5000")
