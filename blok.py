from flask import Flask,render_template,flash,redirect,url_for,session,logging,request
from flask.signals import message_flashed
from flask_mysqldb import MySQL
from wtforms import Form,StringField,TextAreaField,PasswordField,validators
from passlib.hash import sha256_crypt
from functools import wraps
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu sayfa için giriş yapmalısınız!!","danger")
            return redirect(url_for("login"))

    return decorated_function

class RegisterForm(Form):
    name = StringField("İsim Soyisim",validators = [
        validators.Length(min = 4,max = 25)
        ])
    username = StringField("Kullanıcı İsmi",validators = [
        validators.Length(min = 4,max = 25)
        ])
    email = StringField("email adresi")
    password = PasswordField("Parola",validators = [
        validators.DataRequired(message = "Lütfen bir parola belirleyin")
        ,validators.EqualTo(fieldname = "confirm",message = "Parolanız uyuşmuyor")
        ])
    confirm = PasswordField("Parola Doğrula")

class LoginForm(Form):
    username = StringField("Kullanıcı Adı")
    password = PasswordField("Parola")


app = Flask(__name__)

app.secret_key = "batubatu44"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_USER"] = "root"
app.config["MYSQL_PASSWORD"] = ""
app.config["MYSQL_DB"] = "batuhanturk"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"


mysql = MySQL(app)

@app.route("/")
def index():
    return render_template("layout.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/register",methods = ["GET","POST"])
def register():
    form = RegisterForm(request.form)

    if request.method == "POST" and form.validate():
        name = form.name.data
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(form.password.data)

        cursor = mysql.connection.cursor()

        sorgu = "insert into users(name,email,username,password) Values (%s,%s,%s,%s)"

        cursor.execute(sorgu,(name,email,username,password))

        mysql.connection.commit()

        cursor.close()

        flash("Successfully",category="success")

        return redirect(url_for("login"))
    else:
        return render_template("register.html",form = form)

@app.route("/login",methods = {"POST","GET"})
def login():
    form = LoginForm(request.form)
    
    if request.method == "POST":
        username = form.username.data
        password_entered = form.password.data

        cursor = mysql.connection.cursor()

        sorgu= "select * from users where username = %s"

        result = cursor.execute(sorgu,(username,))

        if result > 0:
            data = cursor.fetchone()
            real_password = data["password"]

            if sha256_crypt.verify(password_entered,real_password):
                flash("Başarılı Giriş","success")
                session["logged_in"] = True
                session["username"] = username
                return redirect(url_for("index"))
            else:
                flash("Parola Eşleşmedi","danger")
                return redirect(url_for("login"))
        else:
            flash("böyle bir kullanıcı bulunmuyor...","danger")
            return redirect(url_for("login"))

    return render_template("login.html",form = form)

@app.route("/logout")
def logout():
    session.clear()
    flash("Çıkış başarıyla gerçekleştirildi.","success")
    return redirect(url_for("index"))

@app.route("/dashboard")
@login_required
def dashboard():
    cursor = mysql.connection.cursor()
    sorgu = "select * from articles where author = %s"

    result = cursor.execute(sorgu,(session["username"],))

    if result > 0:
        articles = cursor.fetchall()
        return render_template("dashboard.html",articles = articles)
    else:
        return render_template("dashboard.html")

@app.route("/addarticle",methods = ["GET","POST"])
def addarticle():
    form = ArticleForm(request.form)
    if request.method == "POST" and form.validate():
        title = form.title.data
        content = form.content.data

        cursor = mysql.connection.cursor()

        sorgu = "Insert into articles(Title,author,content) values(%s,%s,%s)"

        cursor.execute(sorgu,{title,session["username"],content})

        mysql.connection.commit()

        cursor.close()

        flash("Başarılı","success")

        return redirect(url_for("dashboard"))

    return render_template("addarticle.html",form = form)

class ArticleForm(Form):
    title =StringField("Makale Başlığı",validators =[validators.Length(min = 5,max = 100)])
    content = TextAreaField("Makale İçeriği",validators =[validators.Length(min =10)])

@app.route("/articles")
def articles():
    cursor = mysql.connection.cursor()

    sorgu = "select * from articles"

    result = cursor.execute(sorgu)
    print(result," asdasd")
    if result > 0:
        articles = cursor.fetchall()
        print(articles)
        return render_template("articles.html",articles = articles)
    else:
        return render_template("articles.html")

@app.route("/article/<string:id>")
def detail_article(id):
    cursor = mysql.connection.cursor()

    sorgu = "Select * from articles where id = %s"

    result = cursor.execute(sorgu,(id,))

    if result> 0:
        article = cursor.fetchone()

        return render_template("article.html",article = article)
    else:
        return render_template("article.html")

@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor = mysql.connection.cursor()

    sorgu = "select * from articles where author = %s and id = %s"

    result = cursor.execute(sorgu,(session["username"],id))

    if result > 0:
        sorgu2 = "delete from articles where id = %s"

        cursor.execute(sorgu2,(id,))

        mysql.connection.commit()

        return redirect(url_for("dashboard"))


    else:
        flash("Bu makaleyi silme yetkiniz yok!!","danger")
        return redirect(url_for("index"))
if __name__ =="__main__":
    app.run(debug = "True")