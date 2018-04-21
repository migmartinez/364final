# SI 364 - Miguel Martinez.

## IMPORT STATEMENTS
import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_script import Manager, Shell
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, TextAreaField, PasswordField, BooleanField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import LoginManager, login_required, logout_user, login_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash

## IGDB API IMPORTS
from igdb_api_python.igdb import igdb
import time, os
import requests, json

## APP CONFIG
app = Flask(__name__)
app.debug = True
app.use_reloader = True
app.config['SECRET_KEY'] = 'hard to guess string from si364'
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://postgres:lolcat123@localhost/migmartFinal"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

## APP SETUP 
manager = Manager(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

## LOGIN CONFIG
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'
login_manager.init_app(app)

## IGDB CONFIG
igdb = igdb('a062d7e1124df2be5e3847535974b8cc')

## MODELS ##

## ASSOCIATION TABLES
games_list = db.Table('games_list',db.Column('list_id',db.Integer, db.ForeignKey('lists.id')),db.Column('game_id',db.Integer, db.ForeignKey('games.id')))

profiles_list = db.Table('profiles_list',db.Column('profile_id',db.Integer, db.ForeignKey('profiles.id')),db.Column('user_id',db.Integer, db.ForeignKey('users.id')))


class Games(db.Model):
    __tablename__ = "games"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(225))
    games = db.relationship('Lists',secondary=games_list,backref=db.backref('games',lazy='dynamic'),lazy='dynamic')

class Lists(db.Model):
    __tablename__ = "lists"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(225))
    listlist = db.Column(db.String(500))

class Profile(db.Model):
    __tablename__ = "profiles"
    id = db.Column(db.Integer, primary_key=True)
    descript = db.Column(db.String(250))
    favgame = db.Column(db.String(64))
    nametag = db.Column(db.String(64))
    username = db.relationship('User', secondary=profiles_list, backref=db.backref('profiles',lazy='dynamic'),lazy='dynamic')

## USER MODELS

# User log in model
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))

    profile = db.relationship('Profile', secondary=profiles_list, backref=db.backref('users',lazy='dynamic'),lazy='dynamic')


    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) # returns User object or None

## FORMS 

class GameListForm(FlaskForm):
    name = StringField("Enter the name of the game list: ", validators=[Required()])
    games = TextAreaField("Enter the games in the following format: name, priority rating -- separated by newlines")
    submit = SubmitField("Submit")


class GameForm(FlaskForm):
    name = StringField("Enter the name of the game: ",validators=[Required(), Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,'Games must have only letters, numbers, dots or underscores, no special characters')])
    submit = SubmitField("Submit")

    def whitespace_check():
        if name.data[0] == ' ':
            raise ValidationError('Field cannot start with a space')


class UpdateForm(FlaskForm):
    submit = SubmitField("Update")

class UpdatePriorityForm(FlaskForm):
    updatePriority = StringField("Enter the new priority rating of the game: ",validators=[Required()])
    submit = SubmitField("Update")

class DeleteButtonForm(FlaskForm):
    submit = SubmitField("Delete")

## LOGIN AND REGISTRATION FORMS

class RegistrationForm(FlaskForm):
    email = StringField('Email:', validators=[Required(),Length(1,64),Email()])
    username = StringField('Username:',validators=[Required(),Length(1,64),Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,'Usernames must have only letters, numbers, dots or underscores')])
    password = PasswordField('Password:',validators=[Required(),EqualTo('password2',message="Passwords must match")])
    password2 = PasswordField("Confirm Password:",validators=[Required()])
    submit = SubmitField('Register User')

    #Additional checking methods for the form
    def validate_email(self,field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self,field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1,64), Email()])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')

class ProfileForm(FlaskForm):
    descript = TextAreaField("Enter in your bio here: ",validators=[Length(1,250)])
    favgame = StringField("What is your favorite video game?", validators=[Length(1,64)])
    nametag = StringField("What is your preferred gamer tag?", validators=[Length(1,64)])
    submit = SubmitField('Submit')


## HELPER FUNCTIONS


def get_games(game_inp):
    from practice_api import get_games_name
    info = get_games_name(game_inp)
    rat = Lists(name = "", listlist=info)
    db.session.add(rat)
    db.session.commit()
    return info

def get_or_create_game(game):
    g = Games.query.filter_by(name=game).first()
    if not g:
        g = Games(name=game)
    db.session.add(g)
    db.session.commit()
    return g

def get_or_create_item(item_string):
    elements = [x.strip().rstrip() for x in item_string.split(",")]
    item = Games.query.filter_by(name=elements[0]).first()
    if item:
        return item
    else:
        item = Games(name=elements[0])
        db.session.add(item)
        db.session.commit()
        return item

def get_or_create_list(name, game_strings=[]):
    l = Lists.query.filter_by(name=name).first()
    if not l:
        l = Lists(name=name, listlist=game_strings)
    for s in game_strings:
        item = get_or_create_item(s)
    db.session.add(l)
    db.session.commit()
    return l
        


## VIEW FUNCTIONS

# Should render basic index/home page for user and render form for entering in game data utilizing IGDB's API. Then save the form data to a database using a get_or_create method. 
@app.route('/', methods=["GET","POST"])
def index():
    form = GameForm()
    if request.method == "POST":
        name = form.name.data
        new_game = get_or_create_game(name)
        gamess = get_games(game_inp=name)
        new_list = get_or_create_list(name, gamess)
        return render_template('games.html', info=gamess)
    return render_template('base.html',form=form)

# Should render page with all game contained on it.
@app.route('/games',methods=["GET","POST"])
def games():
    form = DeleteButtonForm()
    lsts = Lists.query.all()
    input_games = Games.query.all()
    return render_template('games.html', gamez_list=lsts ,form=form, gg=input_games)

## LOGIN ROUTES
@app.route('/login',methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('index'))
        flash('Invalid username or password.')
    return render_template('login.html',form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out')
    return redirect(url_for('index'))

@app.route('/register',methods=["GET","POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,username=form.username.data,password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('You can now log in!')
        return redirect(url_for('login'))
    return render_template('register.html',form=form)

@app.route('/clutchnixon')
@login_required
def clutch():
    return render_template('clutchnixon.html')

@app.route('/profile',methods=["GET", "POST"])
@login_required
def profile():
    form = ProfileForm()
    profile = Profile(descript=form.descript.data,favgame=form.favgame.data,nametag=form.nametag.data)
    db.session.add(profile)
    db.session.commit()
    return render_template('profile.html',form=form)

@app.route('/myprofile')
@login_required
def myprof():
    prof_info = Profile.query.all()
    return render_template('myprofile.html', info=prof_info)

@app.route('/delete/<game>',methods=["GET", "POST"])
def delete(game):
    db.session.delete(Games.query.filter_by(name=game).first())
    flash("Deleted game {}".format(game))
    return redirect(url_for("games"))


## ERROR HANDLING ROUTES
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500



## FINAL
if __name__ == "__main__":
    db.create_all()
    manager.run()
