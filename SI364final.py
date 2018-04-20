# SI 364 - Miguel Martinez.

## IMPORT STATEMENTS
import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_script import Manager, Shell
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FloatField, TextAreaField
from wtforms.validators import Required
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import LoginManager, login_required, logout_user, login_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash

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

# LOGIN CONFIG
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'
login_manager.init_app(app)

## MODELS

## ASSOCIATION TABLE
games_list = db.Table('games_list',db.Column('list_id',db.Integer, db.ForeignKey('lists.id')),db.Column('game_id',db.Integer, db.ForeignKey('games.id')))

class Games(db.Model):
    __tablename__ = "games"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(225))
    games = db.relationship('Lists',secondary=games_list,backref=db.backref('games',lazy='dynamic'),lazy='dynamic')

class Lists(db.Model):
    __tablename__ = "lists"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(225))
    rating = db.Column(db.Integer)

## FORMS 

class GameListForm(FlaskForm):
    name = StringField("Enter the name of the game list: ", validators=[Required()])
    games = TextAreaField("Enter the games in the following format: name, priority rating -- separated by newlines")
    submit = SubmitField("Submit")

class GameForm(FlaskForm):
    name = StringField("Enter the name of the game: ",validators=[Required()])
    submit = SubmitField("Submit")

class UpdateForm(FLaskForm):
    submit = SubmitField("Update")

class UpdatePriorityForm(FlaskForm):
    updatePriority = StringField("Enter the new priority rating of the game: ",validators=[Required()])
    submit = SubmitField("Update")

class DeleteButtonForm(FlaskForm):
    submit = SubmitField("Delete")




## HELPER FUNCTIONS

def get_or_create_game(game):
    elements = [x.strip().rstrip() for x in game.split(",")]
    g = Games.query.filter_by(name=elements[0]).first()
    if g:
        return g
    else:
        g = Games.query.filter_by(name=elements[0],rating=elements[-1])
        db.session.add(g)
        db.session.commit()
        return g

#def get_or_create_list(title)

## VIEW FUNCTIONS

# Should render basic index/home page for user and render form for entering in game data utilizing IGDB's API. Then save the form data to a database using a get_or_create method. When the form is submitted, should redirect to the same page but with an alert notifying the user that the game has been saved to their wish list.
@app.route('/', methods=["GET","POST"])
def index():
    form = GameForm()
    if request.method == "POST":
        title = form.name.data
        new_game = get_or_create_game(title)
    return render_template('base.html',form=form)

# Should render page with all game lists contained on it. User should be able to select, rank, edit, delete, and view the lists
@app.route('/games',methods=["GET","POST"])
def games():
    pass


## FINAL
if __name__ == "__main__":
    db.create_all()
    manager.run()
