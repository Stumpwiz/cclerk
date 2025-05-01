from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models.user import User
from extensions import db
from routes.decorators import role_required, handle_errors
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, HiddenField, ValidationError
from wtforms.validators import DataRequired, Length, EqualTo
import re

# Define a blueprint for admin routes
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Custom email validator that doesn't require email_validator package
def validate_email(form, field):
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, field.data):
        raise ValidationError('Invalid email address')

# Form for creating/editing users
class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), validate_email, Length(max=120)])
    password = PasswordField('Password', validators=[Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[EqualTo('password')])
    role = SelectField('Role', choices=[('user', 'User'), ('admin', 'Admin')], validators=[DataRequired()])

# View all users
@admin_bp.route('/users')
@role_required('admin')
@handle_errors
def view_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

# Add a new user
@admin_bp.route('/users/add', methods=['GET', 'POST'])
@role_required('admin')
@handle_errors
def add_user():
    form = UserForm()

    if form.validate_on_submit():
        # Check if username or email already exists
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists', 'danger')
            return render_template('admin/user_form.html', form=form, action='Add')

        if User.query.filter_by(email=form.email.data).first():
            flash('Email already exists', 'danger')
            return render_template('admin/user_form.html', form=form, action='Add')

        # Create new user
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data
        )
        user.role = form.role.data

        db.session.add(user)
        db.session.commit()

        flash('User added successfully', 'success')
        return redirect(url_for('admin.view_users'))

    return render_template('admin/user_form.html', form=form, action='Add')

# Edit an existing user
@admin_bp.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@role_required('admin')
@handle_errors
def edit_user(id):
    user = User.query.get_or_404(id)
    form = UserForm(obj=user)

    # Don't require password for editing
    form.password.validators = []
    form.confirm_password.validators = []

    if form.validate_on_submit():
        # Check if username already exists (for a different user)
        existing_user = User.query.filter_by(username=form.username.data).first()
        if existing_user and existing_user.id != id:
            flash('Username already exists', 'danger')
            return render_template('admin/user_form.html', form=form, action='Edit', user_id=id)

        # Check if email already exists (for a different user)
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user and existing_user.id != id:
            flash('Email already exists', 'danger')
            return render_template('admin/user_form.html', form=form, action='Edit', user_id=id)

        # Update user
        user.username = form.username.data
        user.email = form.email.data
        user.role = form.role.data

        # Update password if provided
        if form.password.data:
            from werkzeug.security import generate_password_hash
            user.password_hash = generate_password_hash(form.password.data)

        db.session.commit()

        flash('User updated successfully', 'success')
        return redirect(url_for('admin.view_users'))

    return render_template('admin/user_form.html', form=form, action='Edit', user_id=id)

# Delete a user
@admin_bp.route('/users/delete/<int:id>', methods=['POST'])
@role_required('admin')
@handle_errors
def delete_user(id):
    user = User.query.get_or_404(id)

    # Prevent admin from deleting their own account
    if session.get('user_id') == user.id:
        flash('You cannot delete your own account', 'danger')
        return redirect(url_for('admin.view_users'))

    db.session.delete(user)
    db.session.commit()

    flash('User deleted successfully', 'success')
    return redirect(url_for('admin.view_users'))
