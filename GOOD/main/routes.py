from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_user, logout_user, login_required
from GOOD import db
from GOOD.main import bp
from GOOD.main.forms import LoginForm
from GOOD.models import User
from GOOD.grading.routes import create_default_adjudicators, create_default_disciplines_dances, create_default_levels, \
    create_default_dancers, create_default_heats, create_default_couples, assign_default_couples, reset_data


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
    if current_user.is_adjudicator():
        current_user.discipline_id = 0
        current_user.level_id = 0
        current_user.order = None
        current_user.start_page = False
        db.session.commit()
    logout_user()
    return redirect(url_for('main.index'))


@bp.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if current_user.is_adjudicator():
        return redirect(url_for('grading.adjudicate_start_page'))
    if request.method == 'POST':
        if "default" in request.form:
            create_default_adjudicators()
            create_default_disciplines_dances()
            create_default_levels()
            create_default_dancers()
            create_default_heats()
            create_default_couples()
            assign_default_couples()
            return redirect(url_for('main.dashboard'))
        if "reset_data" in request.form:
            reset_data()
            return redirect(url_for('main.dashboard'))
    return render_template('dashboard.html')
