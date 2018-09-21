from flask import Flask, request, render_template, url_for, flash, redirect, session
from forms import Regform, Loginform, Articleform
from functools import wraps
from passlib.hash import sha256_crypt as sha256
import pymysql.cursors
import secrets

app = Flask(__name__)
#for secret key to create unique session
app.secret_key = secrets.token_hex(16)

#Configure database
db = pymysql.connect(host='localhost',user='root',password='',db='flask_blog',cursorclass=pymysql.cursors.DictCursor)

#Index page
@app.route('/')
def index():
    return collect_posts('index.html','Home')

#About Page
@app.route('/about')
def about():
    return render_template('about.html', title='About')

#Register page
@app.route('/register', methods=['GET','POST'])
def register():
    form = Regform(request.form)
    if request.method == 'POST' and form.validate():
        name = request.form['username']
        email = request.form['email']
        password = sha256.encrypt(str(request.form['password'])) #Encrypt password

        #Create cursor
        cs = db.cursor()
        #check if email already exists on database, if it doesn't continue to else statement
        if (check_for_same_email(email)):
            flash(check_for_same_email(email), 'danger')    
        else:
             #Try to catch errors
            try:
                insertquery = 'INSERT INTO users(username, email, password) VALUES(%s, %s, %s)'
                data = (name, email, password)
                #Execute sql query
                cs.execute(insertquery, data)
                #commit changes to database
                db.commit()
                flash('You are now registered and can login', 'success')
                return redirect(url_for('index'))
            except Exception as e:
                db.rollback()
                flash('Something went wrong: ' + str(e), 'danger')
            finally:
                cs.close()

        
    return render_template('register.html', form=form, title='Register')

#Function to check if email already exists in database
def check_for_same_email(email):
    #create cursor
    cs = db.cursor()
    try:
        checkquery = 'SELECT * FROM users WHERE email = %s'
        new_email = (email)
        cs.execute(checkquery, new_email)
        result = cs.fetchone()
        if result:
            return 'Email already exists, choose another email or login!'
    except Exception as e:
        return 'Something went wrong! ' + str(e)

#login page
@app.route('/login', methods=['GET','POST'])
def login():
    form = Loginform(request.form)
    if request.method == 'POST':
        email = request.form['email']
        password_candidate = request.form['password']
        cs = db.cursor()
        try:
            selectquery = 'SELECT username,password FROM users WHERE email = %s'
            result = cs.execute(selectquery, email)
            if (result > 0):
                get_row = cs.fetchone()
                db_password = get_row['password']
                
                #compare passwords
                if sha256.verify(password_candidate, db_password):
                    username = get_row['username']
                    #show info in console
                    app.logger.info('Passwords matched')
                    #Start session
                    session['logged_in'] = True
                    session['username'] = username
                    session['email'] = email
                    flash('You are now logged in!', 'success')
                    return redirect(url_for('dashboard'))
                    
                else:
                    error = 'Username/Password is incorrect!'
                    return render_template('login.html', form=form, error=error)
            else:
                 error = 'Username/Password is incorrect!'
                 return render_template('login.html', form=form, error=error)
        except Exception as e:
            flash('Something went wrong: ' + str(e), 'danger')
            db.rollback()
        finally:
            cs.close()
    return render_template('login.html', form=form, title= 'Login')

#display all articles function
@app.route('/articles', methods=['GET'])
def articles():
    return collect_posts('articles.html','Articles')

# Check if user session is set
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect(url_for('login'))
    return wrap

#collect posts from database
def collect_posts(view, titler):
    cs = db.cursor()
    try:
        collectquery = "SELECT * FROM articles ORDER BY id DESC"
        result = cs.execute(collectquery)
        if result:
            posts = cs.fetchall()
            return render_template(view, posts=posts, title=titler)
        else:
            return render_template(view, title=titler, msg='No posts yet!')
    except Exception as e:
        flash('Something went wrong!' + str(e), 'danger')
        db.rollback()
    finally:
        cs.close()

#getting individual posts to display contents
@app.route('/article/<string:id>/')
def article(id):
    cs = db.cursor()
    data = (id)
    collectquery = "SELECT * FROM articles WHERE id = %s"
    cs.execute(collectquery, data)
    article = cs.fetchone()
    return render_template('article.html', article=article, title='Article | '+article['title'])

#dashboard function
@app.route('/dashboard')
@is_logged_in
def dashboard():
    return collect_posts('dashboard.html', 'Dashboard')

#logout function
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out!', 'success')
    return redirect(url_for('login'))

#add post function
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = Articleform(request.form)
    if request.method == 'POST' and form.validate():
        article_title = request.form['title']
        article_body = request.form['body']
        article_author = session['username']
        data = (article_title, article_body, article_author)
        cs = db.cursor()
        try:
            insertquery = "INSERT INTO articles(title,body,author) VALUES(%s,%s,%s)"
            result = cs.execute(insertquery,data)
            if result:
                db.commit()
                flash('Post Created!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Post not created!', 'danger')
        except Exception as e:
            db.rollback()
            flash('Something went wrong: ' + str(e), 'danger')
        finally:
            cs.close()

    return render_template('add_article.html', title='New Article',form=form)

#Delete Post method
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete(id):
    if request.method == 'POST':
        cs = db.cursor()
        cs.execute("DELETE FROM articles WHERE id = %s",(id))
        db.commit()
        return collect_posts('dashboard.html', 'Dashboard')
    flash('Action not allowed!', 'danger')
    return collect_posts('dashboard.html', 'Dashboard')

@app.route('/edit_article/<string:id>', methods=['POST','GET'])
@is_logged_in
def edit_article(id):
    form = Articleform(request.form)
    cs = db.cursor()
    cs.execute("SELECT * FROM articles WHERE id=%s",[id])
    data = cs.fetchone()

    #Insert into article value
    form.title.data = data['title']
    form.body.data = data['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        cs.execute("UPDATE articles SET title=%s, body=%s WHERE id=%s", (title,body,id))
        db.commit()
        cs.close()

        flash('Post Updated!', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form, title='Edit Article')


#incase someone wants to get into admin
@app.route('/admin')
def admin():
    return redirect('http://www.google.com')

if __name__ == '__main__':
    app.run(debug=True)
