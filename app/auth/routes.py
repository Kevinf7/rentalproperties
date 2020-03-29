from flask import render_template, redirect, url_for, flash, current_app, session
from app.auth import bp
from app.auth.forms import LoginForm


@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        if password != current_app.config['SITE_PASS']:
            flash('Login unsuccessful. Incorrect password.')
        else:
            session['logged_in']=True
            flash('Login successful')
            return redirect(url_for('main.index'))
    return render_template('auth/login.html', form=form)
