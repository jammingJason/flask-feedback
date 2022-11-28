
from flask import Flask, request, redirect, render_template, flash, session
from models import db, connect_db, User, Feedback
from forms import UserForm, LoginForm, FeedbackForm


app = Flask(__name__)
app.config['SECRET_KEY'] = 'SECRET_KEY'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///feedback'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = True
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

connect_db(app)


@app.route('/')
def go_home():
    return redirect('/users')


@app.route('/register', methods=['GET', 'POST'])
def reg_user():
    form = UserForm()
    if form.validate_on_submit():
        un = form.username.data
        pw = form.username.data
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        new_user = User.register(un, pw, email, first_name, last_name)
        db.session.add(new_user)
        db.session.commit()
        session['user_name'] = new_user.username
        return redirect('/users/' + new_user.username)
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def user_login():
    form = LoginForm()
    if form.validate_on_submit():
        un = form.username.data
        pw = form.username.data
        user = User.authenticate(un, pw)
        if user:
            session['user_name'] = user.username
            flash('Welcome Back ' + user.first_name, 'success')
            return redirect('/users/' + user.username)
    return render_template('login.html', form=form)


@app.route('/logout')
def logout():
    session.pop('user_name')
    flash('You have been logged out!', 'warning')
    return redirect('/login')


@app.route('/users/<username>')
def secret_room(username):
    if 'user_name' not in session:
        flash('You must be logged in to view this page', 'danger')
        return redirect('/login')

    user = User.query.get_or_404(username)
    feedback = Feedback.query.filter_by(username=username).all()
    # flash('You made it!', 'success')
    return render_template('secret.html', user=user, feedback=feedback)


@app.route('/users')
def show_all_users():
    users = User.query.all()
    return render_template('users.html', users=users)


@app.route('/users/<username>/delete', methods=['POST'])
def delete_user(username):
    if session['user_name'] == username:
        feedback = Feedback.query.filter_by(username=username).all()
        for fb in feedback:
            delete_post(fb.id)
        user = User.query.get(username)
        db.session.delete(user)
        db.session.commit()
        logout()
        flash('User has been deleted', 'warning')
        return redirect('/users')


@app.route('/users/<username>/feedback/add', methods=['GET', 'POST'])
def add_feedback(username):

    form = FeedbackForm()
    if session['user_name'] == username:
        if form.validate_on_submit():
            title = form.title.data
            content = form.content.data
            fb = Feedback(title=title, content=content, username=username)
            db.session.add(fb)
            db.session.commit()
            return redirect(f"/users/{username}")
    return render_template('feedback.html', form=form)


@app.route('/feedback/<id>/update', methods=['GET', 'POST'])
def update_post(id):
    fb = Feedback.query.get_or_404(id)
    form = FeedbackForm(obj=fb)
    if session['user_name'] == fb.username:
        if form.validate_on_submit():
            title = form.title.data
            content = form.content.data
            feedback = Feedback(id=id, title=title, content=content)
            db.session.merge(feedback)
            db.session.commit()
            return redirect(f"/users/{fb.username}")
    return render_template('edit-feedback.html', form=form, fb=fb)


@app.route('/feedback/<id>/delete', methods=['POST'])
def delete_post(id):
    fb = Feedback.query.get(id)
    if session['user_name'] == fb.username:
        db.session.delete(fb)
        db.session.commit()
        flash('The feedback has been deleted', 'info')
        return redirect(f'/users/{fb.username}')
    flash('You must be logged in as the owner of the feedback to delete it', 'danger')
    return redirect('/login')

    # POST /users/<username>/delete
    # Remove the user from the database and make sure to also delete all of their feedback.
    # Clear any user information in the session and redirect to /.
    # Make sure that only the user who is logged in can successfully delete their account
