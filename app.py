from flask import Flask, request, render_template, redirect, url_for, flash, session, abort
from models import db, connect_db, User, Feedback
from forms import UserForm, LoginForm, FeedbackForm
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///users'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['SECRET_KEY'] = 'secretkey'

connect_db(app)
db.create_all()

@app.route('/')
def index():
    return redirect(url_for('register_page'))

@app.route('/register')
def register_page():
    form = UserForm()
    return render_template('users/register.html', form=form)

@app.route('/register', methods=['POST'])
def add_user():
    form = UserForm()
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        
        try:
            new_user = User.register(username, password, email, first_name, last_name)
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for('secret_page'))
        except IntegrityError:
            db.session.rollback()
            form.username.errors.append('Username already taken')
    
    return render_template('users/register.html', form=form)

@app.route('/login')
def login_page():
    form = LoginForm()
    return render_template('users/login.html', form=form)

@app.route('/login', methods=['POST'])
def login_user():
    form = LoginForm()
    
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        user = User.authenticate(username, password)
        
        if user:
            session['username'] = user.username
            return redirect(url_for('user_details_page', username=user.username))
        else:
            flash("Invalid Username/Password")
            
    return render_template('users/login.html', form=form)

@app.route('/secret')
def secret_page():
    if 'username' in session:
        return render_template('secret.html')
    
    flash('Please login')
    return redirect(url_for('login_page'))

@app.route('/users/<username>')
def user_details_page(username):
    if 'username' not in session:
        flash('Please login')
        return redirect(url_for('login_page'))
    
    if username != session['username']:
         abort(401)
        
    user = User.query.get_or_404(username)
    feedback = user.feedback
        
    form = FeedbackForm()
    return render_template('users/details.html', user=user, form=form, feedback=feedback)

@app.route('/logout')
def logout():
    session.pop('username')
    return redirect(url_for('login_page'))

@app.route('/users/<username>/delete', methods=['POST'])
def delete_user(username):
    if 'username' not in session or username != session['username']:
        abort(401)
        
    user = User.query.get(username)
    db.session.delete(user)
    db.session.commit()
    session.pop('username')
    return redirect(url_for('login_page'))

@app.route('/users/<username>/feedback/add', methods=['POST'])
def add_feedback(username):
    user = User.query.get_or_404(username)
    
    if 'username' not in session or username != session['username']:
        abort(401)
    
    form = FeedbackForm()
    title = form.title.data
    content = form.content.data
    new_feedback = Feedback(title=title, content=content, username=username)
    db.session.add(new_feedback)
    db.session.commit()
    return redirect(url_for('user_details_page', username=username))

@app.route('/feedback/<feedback_id>/update')
def update_feedback_page(feedback_id):
    feedback = Feedback.query.get_or_404(feedback_id)
    
    if 'username' not in session or feedback.username != session['username']:
        abort(401)
        
    form = FeedbackForm(obj=feedback)
    return render_template('users/feedback.html', feedback=feedback, form=form)

@app.route('/feedback/<feedback_id>/update', methods=['POST'])
def update_feedback(feedback_id):
    feedback = Feedback.query.get_or_404(feedback_id)
    
    if 'username' not in session or feedback.username != session['username']:
        abort(401)
    
    feedback.title = request.form['title']
    feedback.content = request.form['content']
    db.session.commit()
    return redirect(url_for('user_details_page', username=feedback.username))

@app.route('/feedback/<feedback_id>/delete', methods=['POST'])
def delete_feedback(feedback_id):
    feedback = Feedback.query.get_or_404(feedback_id)
    
    if 'username' not in session or feedback.username != session['username']:
        abort(401)
    
    db.session.delete(feedback)
    db.session.commit()
    return redirect(url_for('user_details_page', username=feedback.username))