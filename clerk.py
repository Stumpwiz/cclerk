from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from config import Config

# Initialize Flask app
app = Flask(__name__)

# Configure app using config.py
app.config.from_object(Config)

# Initialize the database
db = SQLAlchemy(app)


# User model for authentication
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), nullable=False, unique=True)
    password_hash = db.Column(db.String(256), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# Sample CRUD model
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)


# Create database tables
@app.before_first_request
def create_tables():
    db.create_all()


# Routes
@app.route('/')
def index():
    # Redirect to login if user is not authenticated
    if not session.get('user_id'):
        return redirect(url_for('login'))
    return render_template('home.html', items=Item.query.all())


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))


# CRUD routes (example for managing "Item" objects)
@app.route('/crud', methods=['GET', 'POST'])
def crud():
    if not session.get('user_id'):
        return redirect(url_for('login'))
    items = Item.query.all()
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description')
        new_item = Item(name=name, description=description)
        db.session.add(new_item)
        db.session.commit()
        flash('Item added successfully!', 'success')
        return redirect(url_for('crud'))
    return render_template('crud.html', items=items)


@app.route('/delete/<int:item_id>')
def delete_item(item_id):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    item = Item.query.get(item_id)
    if item:
        db.session.delete(item)
        db.session.commit()
        flash('Item deleted successfully!', 'success')
    else:
        flash('Item not found', 'danger')
    return redirect(url_for('crud'))


if __name__ == '__main__':
    app.run(debug=True)
