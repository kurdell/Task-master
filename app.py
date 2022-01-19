from flask import Flask, redirect, render_template, request, session, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import re

# Configure application
app = Flask(__name__)

# Add database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db = SQLAlchemy(app)

# Create  users model 
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    password = db.Column(db.String, nullable=False)

    # Create string
    def __repr__(self):
        return '<Name %r>' % self.name

class Tasks(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String)
    goals = db.Column(db.String)
 
    # Create string
    def __repr__(self):
        return '<Tasks %r>' % self.task

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

# Session secret key
app.secret_key = "869030e617225992a22e214225c9c9fdfdaeef8d7bbc1bf291812392f8c68861"

# Decorator function for login_required (https://flask.palletsprojects.com/en/2.0.x/patterns/viewdecorators/)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('user') is None:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
@login_required
def index():

    # Show tasks
    task_list = Tasks.query.all()
    user = session['user']
    return render_template("index.html", task_list = task_list, user = user)

@app.route('/login', methods=['GET', 'POST'])
def login():

    # Forget pervious user
    session.pop('user', None)

    # Check info entered in form 
    if request.method == "POST":
        usr_name = request.form.get("name")
        usr_password = request.form.get("password")

        if not usr_name:
            flash ('Must provide username')
            return redirect(url_for('login'))

        # Ensure password was submitted
        elif not usr_password:
            flash ('Must provide password')
            return redirect(url_for('login'))
            

        check_usr = Users.query.filter_by(name=usr_name).first()

        # Validate username and password against database info and log user in
        try:
            if check_usr.name != usr_name or not check_password_hash(check_usr.password, usr_password):
                flash ('Incorrect Username/Password')
            else:
                session['user'] = usr_name
                return redirect(url_for('index'))
            
        except AttributeError:
            flash ('Incorrect Username/Password')
            return redirect(url_for('login'))
            
            
    return render_template("login.html")

        

  
        
@app.route("/logout")
def logout():
    # Clear session and display info to user
    if 'user' in session:
        user = session['user']
        flash(f'You have been logged out, {user}', 'info')
    session.pop('user', None)

    # Redirect to login
    return redirect(url_for('index'))
        


@app.route("/register", methods=["GET", "POST"]) 
def register():
    
    # Forget previous user
    session.pop('user', None)

    # Display registration form
    if request.method == "GET":
        return render_template("register.html")
    
    # Validate info entered
    if request.method == "POST":
        usr_name = request.form.get("name")
        usr_password = request.form.get("password")
        usr_confirm = request.form.get("confirm")
        check_usr = Users.query.filter_by(name=usr_name).first()

        # Ensure username was submitted
        if not usr_name:
            flash ('Must provide Username')
            return redirect(url_for('register'))
        
        # Ensure username does not exist
        if check_usr is not None:
            flash ('Username already exists')
            return redirect(url_for('register'))

        # Check if user submitted password
        if not usr_password:
            flash ('Must provide Password')
            return redirect(url_for('register'))
        
        # validate password length
        if len(usr_password) < 8:
            flash ('Password must include least 8 characters, an uppercase letter and a number')
            return redirect(url_for('register'))
        
        if re.search('[0-9]',usr_password) is None:
            flash ('Password must include least 8 characters, an uppercase letter and a number')
            return redirect(url_for('register'))

        if re.search('[A-Z]',usr_password) is None:
            flash ('Password must include least 8 characters, an uppercase letter and a number')
            return redirect(url_for('register'))

        # Check if user re-typed password  
        if not usr_confirm:
            flash ('Please re-type your password')
            return redirect(url_for('register'))
        
        # Check if passwords match
        if usr_confirm != usr_password:
            flash ('Passwords do not match')
            return redirect(url_for('register'))
        
        # Hash user password before storing in database
        hash = generate_password_hash(usr_password)

        # Add user to database
        user = Users(name=usr_name , password=hash)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('index'))

@app.route("/task", methods=["GET", "POST"])
@login_required
def task():
    if request.method == "GET":
        return render_template("task.html")
    
    if request.method == "POST":
        task_entered = request.form.get("task")

        # Add task to database
        usr_task = Tasks(task=task_entered)
        db.session.add(usr_task)
        db.session.commit()
        return redirect(url_for('index'))
    

@app.route("/notes", methods=["GET", "POST"])
@login_required
def goals():
    if request.method == "GET":
        return render_template("goals.html")


if __name__ == "__main__":
    app.run(debug=False)