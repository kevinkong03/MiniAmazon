from flask import render_template, request, flash
from flask import current_app as app
from flask_login import current_user
from flask_wtf import FlaskForm
from wtforms import FloatField, StringField, SubmitField, PasswordField, validators
from wtforms.validators import DataRequired, NumberRange, ValidationError, EqualTo, NumberRange
from flask_paginate import Pagination
from datetime import datetime

from .models.balance import Balance
from .models.user import User
from flask import redirect, url_for 

from flask import Blueprint, jsonify

bp = Blueprint('account', __name__)

class EditProfileForm(FlaskForm):
    firstname = StringField('First Name', validators=[DataRequired()])
    lastname = StringField('Last Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired()])
    submit = SubmitField('Update Information')

    def validate_email(self, email):
        if User.email_exists(email.data) and email.data != current_user.email:
            raise ValidationError('Email already exists.')
        

class PasswordForm(FlaskForm):
    password = PasswordField('New Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Update Password')

@bp.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    """ 
    Edit profile page except for password
    """
    if not current_user.is_authenticated:
        flash('Not logged in.', 'error')
        return redirect(url_for('users.login'))

    form = EditProfileForm()
    user = User.get(current_user.id)

    if form.validate_on_submit():

        if User.update_user_information(current_user.id, form.firstname.data, form.lastname.data, form.email.data, form.address.data):
            flash('Your information has been updated successfully!')
            return redirect(url_for('account.account'))
        else:
            flash('Something went wrong. Try again later.')

    else:

        form.firstname.data = user.firstname
        form.lastname.data = user.lastname
        form.email.data = user.email
        form.address.data = user.address

    return render_template('account_edit_profile.html', form=form, user=user)

@bp.route('/change_password', methods=['GET', 'POST'])
def change_password():
    """
    Change password page
    """
    if not current_user.is_authenticated:
        flash('Not logged in.', 'error')
        return redirect(url_for('users.login'))
    
    form = PasswordForm()
    if form.validate_on_submit():
        if User.update_user_password(current_user.id, form.password.data):
            flash('Your password has been updated successfully!')
            return redirect(url_for('account.account'))
    return render_template('account_change_password.html', form=form)


class KForm(FlaskForm):

    withdraw_val = FloatField(label="Withdraw", validators=[DataRequired()])
    reload_val = FloatField(label="Reload", validators=[DataRequired()])

@bp.route('/account')
def account():
    return render_template('account.html')

@bp.route('/balance', methods=['GET', 'POST'])
def balance():
    # Set the page, per_page, and total pages for pagination
    page = request.args.get('page', type=int, default=1)
    per_page = 10

     # Calculate the offset 
    offset = (page - 1) * per_page

    balance_history = []
    total = 0
    
    if current_user.is_authenticated:
        # Get the current balance from the database using the Balance class
        balance_history = Balance.get_balance_history_by_uid(current_user.id,offset,per_page)
        current_balance = Balance.get_current_balance_by_uid(current_user.id)
        total = Balance.get_total_balances_by_user(current_user.id)
        pagination = Pagination(page=page, per_page=per_page, total=total)
        months, average_amounts = Balance.get_months_average_by_uid(current_user.id)
        added_balance = None

        if request.method == 'POST':
            
            form = KForm(request.form)
        
            # Process the transactions
            #if form.validate_on_submit():
            if 'withdraw' in request.form:
                
                withdrawal_amount = round(form.withdraw_val.data, 2)

                if withdrawal_amount <= 0:
                    flash('You must withdraw at least 0.01.', 'error')
                    return redirect(url_for('account.balance'))
                
                if withdrawal_amount <= current_balance:
                    current_balance -= withdrawal_amount
                else:
                    flash('You do not have enough balance to withdraw that amount.', 'error')
                    return redirect(url_for('account.balance'))
                
                added_balance = Balance.add_balance(
                    current_user.id, 
                    datetime.now(), 
                    current_balance,
                    'Withdraw',
                    None
                )
            elif 'reload' in request.form:
        
                reload_amount = round(form.reload_val.data, 2)

                if reload_amount <= 0:
                    flash('You must reload at least 0.01.', 'error')
                    return redirect(url_for('account.balance'))

                current_balance += reload_amount
                added_balance = Balance.add_balance(
                    current_user.id, 
                    datetime.now(), 
                    current_balance,
                    'Reload',
                    None
                )
            

            if added_balance:
                flash('Operation successful!')
                return redirect(url_for('account.balance'))
            else:
                flash('Operation failed.')
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f'{field.capitalize()}: {error}', 'error')
            
        else:
            form = KForm()

        return render_template('balance.html', form=form, balance_history=balance_history, current_balance=current_balance, pagination=pagination, months=months, average_amounts=average_amounts)
    
    # Handle cases where the user is not authenticated or not found
    return render_template('balance.html', form=None, balance_history=None, current_balance=None, pagination=None, months=None, average_amounts=None)