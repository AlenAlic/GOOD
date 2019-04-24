from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import current_user, login_user, logout_user, login_required
from GOOD.main import bp
from GOOD.main.forms import LoginForm
from GOOD.models import User


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'alert-danger')
            return redirect(url_for('main.index'))
        if user.is_active:
            login_user(user)
            return redirect(url_for('main.dashboard'))
    return render_template('index.html', title='Home', login_form=form)


@bp.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


@bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    if current_user.is_adjudicator():
        return redirect(url_for('adjudication_system.adjudicator_dashboard'))
    if current_user.is_floor_manager():
        return redirect(url_for('adjudication_system.floor_manager_start_page'))
    return render_template('dashboard.html')
