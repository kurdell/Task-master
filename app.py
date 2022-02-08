from asyncio.windows_events import NULL
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

# Create Task table
class Tasks(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String)
 
    # Create string
    def __repr__(self):
        return '<Tasks %r>' % self.task

# Create Notes table
class Notes(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    note_id = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.String)
 
    # Create string
    def __repr__(self):
        return '<Notes %r>' % self.notes

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


# --------------------Routes/Views-------------------------


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():

    # Query database task info to display it
    user = session['user']
    check_user = Users.query.filter_by(name = session['user']).first()
    task_list = Tasks.query.with_entities(Tasks.task).filter_by(user_id = check_user.id)
     
    return render_template("index.html", task_list = task_list, user = user)


@app.route("/delete_task/<task>")
@login_required
def delete_task(task):
    
    delete = Tasks.query.filter_by(task = task).delete()
    db.session.commit()
    return redirect(url_for('index'))

@app.route("/delete_note/<note>")
@login_required
def delete_note(note):
    
    delete = Notes.query.filter_by(notes = note).delete()
    db.session.commit()
    return redirect(url_for('notes'))

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
        user = session['user'].title()
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

        #Log user in to database
        session['user'] = usr_name
        return redirect(url_for('index'))
        
@app.route("/task", methods=["GET", "POST"])
@login_required
def task(): 
    if request.method == "GET":
        return render_template("task.html")

    if request.method == "POST":
        task_entered = request.form.get("task").strip()
        check_user = Users.query.filter_by(name = session['user']).first()

        # Add task to database for logged in user and redirect to homepage
        usr_task = Tasks(task=task_entered, user_id=check_user.id)

        db.session.add(usr_task)
        db.session.commit()
        return redirect(url_for('index'))
    

@app.route("/notes", methods=["GET", "POST"])
@login_required
def notes():

    if request.method == "GET":
        # Query database for user/notes info
        check_user = Users.query.filter_by(name = session['user']).first()
        notes_list = Notes.query.with_entities(Notes.notes).filter_by(note_id = check_user.id)

        return render_template('notes.html' , notes_list = notes_list)

    if request.method == "POST":
         # Query database for user/notes info
        notes = request.form.get("notes").strip()
        check_user = Users.query.filter_by(name = session['user']).first()
        notes_list = Notes.query.with_entities(Notes.notes).filter_by(note_id = check_user.id)

        # Add notes to database for logged in user and redirect to homepage
        usr_notes = Notes(notes=notes, note_id=check_user.id)

        db.session.add(usr_notes)
        db.session.commit()
        return redirect(url_for('notes'))
        
    
        

if __name__ == "__main__":
    db.create_all()
    app.run(debug=True)