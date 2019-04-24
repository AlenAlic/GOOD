from flask import render_template
from GOOD import db
from GOOD.errors import bp
import traceback


@bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html', e=error)


@bp.app_errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html', e=error)


@bp.app_errorhandler(Exception)
def handle_unexpected_error(error):
    db.session.rollback()
    message = traceback.format_exc()
    message = message.split('\n')
    return render_template('errors/500.html', message=message, e=error)
