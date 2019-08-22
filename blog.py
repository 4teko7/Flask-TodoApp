from flask import Flask,render_template,url_for,flash,redirect,session,logging,request
from wtforms import Form,StringField,TextAreaField,PasswordField,validators,Label
from passlib.hash import sha256_crypt
from flask_mysqldb import MySQL
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = "tekomakeleler"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "makaledb"
app.config["MYSQL_CURSORCLASS"]="DictCursor"
mysql = MySQL(app)


con = sqlite3.connect("makaledb")
cursor = con.cursor()
createUserTable = "create table if not exists users(id INT,name TEXT, username TEXT,password TEXT,email TEXT)"
cursor.execute(createUserTable)

createComment = "create table if not exists comment(name TEXT,comment TEXT,date datetime default current_timestamp)"
cursor.execute(createComment)


createArticleTable = "create table if not exists articles(id INTEGER PRIMARY KEY AUTOINCREMENT,title TEXT,author TEXT,content TEXT,date datetime default current_timestamp)"
cursor.execute(createArticleTable)

createInfoTable = "create table if not exists info(username Text,name TEXT,age TEXT,school TEXT,department TEXT,summary TEXT,date datetime default current_timestamp)"
cursor.execute(createInfoTable)

con.commit()
cursor.close()

#Logging Required
def adminLoginRequired(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'adminLogging' in session:
            return f(*args, **kwargs)
        else:
            flash("please login !")
            return redirect(url_for('admin'))

    return wrap

def loginRequired(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logging' in session:
            return f(*args, **kwargs)
        else:
            flash("please login !")
            return redirect(url_for('login'))

    return wrap
#MainPage Comment
class CommentForm(Form):
    name = StringField("Name",validators=[validators.DataRequired(message="lutfen doldurun.")])
    comment = TextAreaField("Comment",validators=[validators.DataRequired(message="lutfen doldurun")])

#About Form
class AboutForm(Form):
    name = StringField("Name and Surname",validators=[validators.DataRequired(message= "Please Fill in the Blank"),validators.length(min=2,max=30)])
    age = StringField("Age")
    school = StringField("School")
    department = StringField("Department")
    summary = TextAreaField("Summary")

#Kullanici Kayit Formu
class RegisterForm(Form):
    name = StringField("Isim Soyisim",validators=[validators.length(min=4,max=25),validators.DataRequired(message="Lutfen Doldurun")])
    username = StringField("Kullanici Adi",validators = [validators.length(min=4,max=25),validators.DataRequired(message="Lutfen Doldurun")])
    password = PasswordField("Parola",validators = [
        validators.length(min = 6,max = 25),
        validators.EqualTo(fieldname = "confirm",message = "parolalar uyusmuyor"),validators.DataRequired(message="Lutfen Doldurun")])
    confirm = PasswordField("Parola Dogrula")
    email = StringField("Email",validators = [validators.Email(message = "Lutfen Gecerli bir email girin"),validators.length(min=10,max=40),validators.DataRequired(message="Lutfen Doldurun")])

#Remove User
class RemoveUser(Form):
    username = StringField("Username",validators=[validators.length(min=4,max=25)])
#Login Form
class LoginForm(Form):
    username = StringField("Kullanici Adi",validators = [validators.DataRequired(message="Lutfen Doldurun")])
    password = PasswordField("Parola",validators=[validators.length(min=6,max=25),validators.DataRequired(message="Lutfen Doldurun")])

#Article Form
class ArticleForm(Form):
    title = StringField("Title",validators=[validators.DataRequired(message="luften doldurun")])
    content = TextAreaField("Content",validators=[validators.length(min=10),validators.DataRequired(message="Lutfen Doldurun")])

@app.route("/")
def index():
    return render_template("index.html")


#REGISTER GET AND POST
@app.route("/register",methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)
    if(request.method == "POST" and form.validate()):
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        con = sqlite3.connect("makaledb")
        cursor = con.cursor()
        cursor.execute("select * from users where username = ?",(username,))
        dataList = cursor.fetchall()
        if(len(dataList) == 0): 
            req = "insert into users(name,username,password,email) VALUES(?,?,?,?)"
            cursor.execute(req,(name,username,password,email))
            con.commit()
            flash("Basariyla Kayit Oldunuz","success")
            cursor.close()
            return redirect(url_for("login"))
        else:
            flash("Bu Isimde Baska Bir Kullanici Var","warning")
            return redirect(url_for("register"))
    else:
        return render_template("register.html",form=form)

@app.route("/removeuser",methods=["GET","POST"])
@adminLoginRequired
def removeuser():
    form = RemoveUser(request.form)
    if(request.method == "POST"):
        username = form.username.data
        con = sqlite3.connect("makaledb")
        cursor = con.cursor()
        cursor.execute("select * from users where username = ?",(username,))
        list = cursor.fetchone()
        if(list != None):
            remove = "delete from users where username = ?"
            cursor.execute(remove,(username,))
            cursor.close()
            con.commit()
            flash("Removed successfully","success")
            return redirect(url_for("removeuser"))
        else:
            flash("There is not such an user","warning")
            return redirect(url_for("removeuser"))
    else:
        return render_template("removeuser.html",form=form)

@app.route("/admin",methods=["GET","POST"])
def admin():
    form = LoginForm(request.form)
    if(request.method == "POST"):
        username = form.username.data
        password = form.password.data
        con = sqlite3.connect("makaledb")
        cursor = con.cursor()
        data = "select * from users where username = ?"
        cursor.execute(data,(username,))
        list = cursor.fetchall()
        if(len(list) != 0):
            adminPassword = "$5$rounds=535000$MxiLzFEfGSRyZ0Im$P.wE9dFwNLBkIYMbpuFF5N/XcN3LZ1fzCIHisk0BKW6"
            if(sha256_crypt.verify(password,adminPassword)):
                flash("giris basarili","success")
                session["logging"] = True
                session["adminLogging"] = True
                session["username"] = username
                return render_template("admin.html",form=form,session=session)
            else:
                if(username != "teko"):
                    flash("You are not an admin","danger")
                    return redirect(url_for("admin"))
                else:
                    flash("parolaniz yanlis","warning")
                    return redirect(url_for("admin"))
        else:
            flash("Giris basarisiz","danger")
            return redirect(url_for("admin"))

    else:
        return render_template("admin.html",form=form)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route("/login",methods=["GET","POST"])
def login():

    form = LoginForm(request.form)
    if request.method == "POST":
        username = form.username.data
        passwordEntered = form.password.data
        con = sqlite3.connect("makaledb")
        cursor = con.cursor()
        req = "select * from users where username = ?"
        cursor.execute(req,(username,))
        data = cursor.fetchall()
        if(len(data) != 0):
            if(sha256_crypt.verify(passwordEntered,data[0][3])):
                flash("Giris Basarili","success")
                session["logging"] = True
                session["username"] = username
                return render_template("dashboard.html",session=session)
            else:
                flash("Giris Basarisiz","danger")
                return redirect(url_for("login"))
        else:
            flash("Giris basarisiz","danger")
            return redirect(url_for("login"))
    else:
        return render_template("login.html",form=form)


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/addarticle",methods=["GET","POST"])
@loginRequired
def addArticle():
    form = ArticleForm(request.form)
    if(request.method == "POST" and form.validate()):
        title = form.title.data
        content = form.content.data
        author = session["username"]
        con = sqlite3.connect("makaledb")
        cursor = con.cursor()
        addArticle = "insert into articles(title,author,content) VALUES(?,?,?)"
        cursor.execute(addArticle,(title,author,content))
        con.commit()

        flash("Article added Successfully","success")
        return redirect(url_for("myArticles"))

    else:
        return render_template("addArticle.html",form=form)

@app.route("/myArticles")
def myArticles():
    con = sqlite3.connect("makaledb")
    cursor = con.cursor()
    cursor.execute("select * from articles where author = ?",(session["username"],))
    list = cursor.fetchall()
    if(len(list) != 0):
        return render_template("/myArticles.html",articles = list)
    else:
        return render_template("myArticles.html",articles=list)

@app.route("/articles",methods=["GET","POST"])
def articles():
    form = CommentForm(request.form)
    con = sqlite3.connect("makaledb")
    cursor = con.cursor()
    if(request.method == "POST" and form.validate()):
        name = form.name.data
        comment = form.comment.data
        form.comment.data = ""
        req = "insert into comment(name,comment) VALUES(?,?)"
        cursor.execute(req,(name,comment))
        con.commit()
    cursor.execute("select * from comment")
    commentList = cursor.fetchall()
    cursor.execute("select * from articles")
    list = cursor.fetchall()
    if(len(list) != 0):
        return render_template("articles.html",articles=list,commentList=commentList,form=form)
    else:
        flash("There is no articles","warning")
        return render_template("articles.html",articles=list,commentList=commentList,form=form)

@app.route("/article/<string:id>")
def article(id):
    con = sqlite3.connect("makaledb")
    cursor = con.cursor()
    cursor.execute("select * from articles where id = ?",(id,))
    list = cursor.fetchone()
    if(list != None):
        content = list[3]
        return render_template("article.html",article = list,content = content)
    else:
        flash("This article is not available") 
        return redirect(url_for("articles"))

@app.route("/editArticle/<string:id>",methods=["GET","POST"])
@loginRequired
def editArticle(id):
    form = ArticleForm(request.form)
    con = sqlite3.connect("makaledb")
    cursor = con.cursor()
    req2 = "select * from articles where id = ?"
    cursor.execute(req2,(id,))
    article = cursor.fetchone()
    if(article != None):
        if(request.method == "POST" and form.validate()):
            title = form.title.data
            content = form.content.data
            #req1 = "insert into articles(title,author,content) VALUES(?,?,?)"
            req1 = "update articles set title = ?, content = ? where id = ?"
            #cursor.execute(req1,(title,session["username"],content))
            cursor.execute(req1,(title,content,id))
            con.commit()
            cursor.close()
            return redirect(url_for("myArticles"))
        else:
            form.title.data = article[1]
            form.content.data = article[3]
            return render_template("editArticle.html",form=form)
    else:
        return render_template("editArticle.html",form=form)

@app.route("/removeArticle/<string:id>")
@loginRequired
def removeArticle(id):
    con = sqlite3.connect("makaledb")
    cursor = con.cursor()
    req = "delete from articles where id = ?"
    cursor.execute(req,(id,))
    flash("Removed Successfully","success")
    con.commit()
    cursor.close()
    return redirect(url_for("myArticles"))

@app.route("/about")
def about():
    if(len(session) != 0):
        con = sqlite3.connect("makaledb")
        cursor = con.cursor()
        req2 = "select * from info where username = ?"
        cursor.execute(req2,(session["username"],))
        info = cursor.fetchone()
        return render_template("about.html",session=session,info=info)
    else :
        return render_template("about.html")

@app.route("/editAbout",methods=["GET","POST"])
@loginRequired
def editAbout():
 
        form = AboutForm(request.form)
        con = sqlite3.connect("makaledb")
        cursor = con.cursor()
        req2 = "select * from info where username = ?"
        cursor.execute(req2,(session["username"],))
        info = cursor.fetchone()
        if(request.method == "POST" and form.validate()):
            name = form.name.data
            age = form.age.data
            school = form.school.data
            summary = form.summary.data
            department = form.department.data

            con = sqlite3.connect("makaledb")
            cursor = con.cursor()
            if(info != None):
                req = "update info set name = ?, age = ?, school = ?, summary = ? where username = ?"
                cursor.execute(req,(name,age,school,summary,session["username"]))
            else:
                req = "insert into info(username,name,age,school,department,summary) VALUES (?,?,?,?,?,?)"
                cursor.execute(req,(session["username"],name,age,school,department,summary))
            con.commit()
            cursor.close()
            return redirect(url_for("about")) 
            
        elif request.method == "GET" and info != None:
            form = AboutForm()
            form.name.data = info[1]
            form.age.data = info[2]
            form.school.data = info[3]
            form.department.data = info[4]
            form.summary.data = info[5]
            return render_template("editAbout.html",form=form,session=session)
        elif request.method == "GET" and info == None:
            return render_template("editAbout.html",form=form,session=session)

@app.route("/search",methods=["GET","POST"])
def search():
    if(request.method == "GET"):
        return redirect(url_for("index"))
    else:
        con = sqlite3.connect("makaledb")
        cursor = con.cursor()
        key/word = request.form.get("keywords")
        req = "select * from articles where title like '%"+keyword+"%'"
        cursor.execute(req)
        list = cursor.fetchall()
        return render_template("search.html",articles=list)

if(__name__ == "__main__"):
    app.run(debug = True)