from functools import wraps
from flask import redirect, session, url_for, flash


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            session['logged_in'] = False
        if session['logged_in'] == False:
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
