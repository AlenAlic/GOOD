from flask import Flask, g, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, AnonymousUserMixin, current_user
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from wtforms import PasswordField
import GOOD.values as values


class MyAdminIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        if not current_user.is_authenticated:
            return redirect(url_for('main.index'))
        else:
            return self.render(self._template)


db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
admin = Admin(template_mode='bootstrap3', index_view=MyAdminIndexView())


class MainView(ModelView):
    column_hide_backrefs = False
    page_size = 1000

    def is_accessible(self):
        if current_user.is_authenticated:
            return True
        return False

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('main.index'))


class UserView(MainView):
    column_exclude_list = ['password_hash', ]
    form_excluded_columns = ['password_hash', ]
    form_extra_fields = {'password2': PasswordField('Password')}

    # noinspection PyPep8Naming
    def on_model_change(self, form, User, is_created):
        if form.password2.data != '':
            User.set_password(form.password2.data)


class Anonymous(AnonymousUserMixin):
    @staticmethod
    def is_admin():
        return False

    @staticmethod
    def is_adjudicator():
        return False


def create_app():
    # Import Models
    from GOOD.models import User

    # Create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object('config')
    app.config.from_pyfile('config.py')

    # Init add-ons
    db.init_app(app)
    migrate.init_app(app, db, render_as_batch=app.config['SQLALCHEMY_DATABASE_URI'].startswith('sqlite:'))
    login.init_app(app)
    login.login_view = 'main.index'
    login.anonymous_user = Anonymous
    admin.init_app(app)
    admin.add_view(UserView(User, db.session))

    # Shell command for creating admin account
    def create_admin(admin_password):
        with app.app_context():
            user = User()
            user.username = 'admin'
            user.set_password(admin_password)
            user.is_active = True
            user.access = values.ACCESS[values.ADMIN]
            db.session.add(user)
            db.session.commit()

    @app.shell_context_processor
    def make_shell_context():
        return {'create_admin': create_admin}

    @app.before_request
    def before_request_callback():
        g.values = values

    # Register blueprints
    from GOOD.main import bp as main_bp
    app.register_blueprint(main_bp)

    from GOOD.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    return app
