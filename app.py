
from flask import Flask
from flask import render_template
from flask import flash, request, redirect, url_for, session, logging

from flask_mysqldb import MySQL               # you have to install "flask-mysqldb" like this: pip install flask-mysqldb
                                                # ifyou get an error install like this: sudo apt install libmysqlclient-devls
                                                # a documentation you can find here: http://flask-mysqldb.readthedocs.io/en/latest/

from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from functools import wraps


app = Flask(__name__)

#Config MySQL
app.config['MYSQL_HOST'] = '127.0.0.1'                  # here was a problem if you use localhost instead - always use 127.0.0.1
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'simple'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
#init MySQL
mysql = MySQL(app)


@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/articles')
def articles():
    return render_template('articles.html')

# Register From Class
class RegisterForm(Form):                       # you will find the documentation here: https://wtforms.readthedocs.io/en/stable/forms.html#the-form-class
    name = StringField('Name', [validators.Length(min=1, max=50)])
    username = StringField('Username', [validators.Length(min=4, max=25)])
    email = StringField('Email', [validators.Length(min=6, max=25)])
    password = PasswordField('Password', [
        validators.data_required(),
        validators.equal_to('confirm', message='Passwords do not match')
    ])
    confirm = PasswordField('Confirm Password')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = sha256_crypt.encrypt(str(form.password.data))

        #create cursor    like this here  http://flask-mysqldb.readthedocs.io/en/latest/
        cur = mysql.connection.cursor()

        #execute query
        cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

        #Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()

        flash('You are now registered and can log in', 'success')

        return redirect(url_for('login'))      #return to index.html
    return render_template('register.html', form=form)

# UserLogin

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method =='POST':
        #get form fields
        username = request.form['username']
        password_candidate = request.form['password']

        #create cursor
        cur = mysql.connection.cursor()

        #get user by username
        result = cur.execute("SELECT * FROM users WHERE username = %s",[username])


        if result > 0:
            #get stored hash
            data = cur.fetchone()           # if there are more then on users he will take the first one
            password = data['password']

            #compare passwords
            if sha256_crypt.verify(password_candidate, password):            # compares the passwords
                #app.logger.info('PASSWORD MATCHED')                         # create an outout on console

                #if Passed
                session['logged_in'] = True                                     # comes from Flask, ist included above
                session['username'] = username

                flash('You are now logged in', 'success')
                return redirect(url_for('dashboard'))


            else:
                #app.logger.info('PASSWORD NOT MATCHED')
                error = 'Invalid login'
                return render_template('login.html', error=error)

            #Close connection
            cur.close()
        else:
            #app.logger.info('NO USER')
            error = 'Username not found'
            return render_template('login.html', error=error)



    return render_template('login.html')


#check if user is logged in                                    #http://flask.pocoo.org/snippets/category/decorators/
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap







# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You are logged out', 'success')
    return redirect(url_for('login'))


# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():

    #create cursor
    cur = mysql.connection.cursor()

    #get article
    result = cur. execute("SELECT * FROM articles")
    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No Articles found'    
        return render_template('dashboard.html', msg)
    
    cur.close()

#Article Form Class
class ArticleForm(Form):                       # you will find the documentation here: https://wtforms.readthedocs.io/en/stable/forms.html#the-form-class
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])
 

# Add Articles
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        #create cursor    like this here  http://flask-mysqldb.readthedocs.io/en/latest/
        cur = mysql.connection.cursor()

        #execute query
        cur.execute("INSERT INTO articles(title, body, autor) VALUES(%s, %s, %s)", (title, body, session['username']))

        #Commit to DB
        mysql.connection.commit()

        #Close connection
        cur.close()


        flash('Article Created', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)



# https://ckeditor.com/ckeditor-4/download/



if __name__ == '__main__':

    app.secret_key="key123"                         # its a session key I think, its needed to secure the session !?

    #app.run()                                     # works with: app.run()
    app.run(debug=True)                            # this starts the app in debug mode und refesh after changes automatically
