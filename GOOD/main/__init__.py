from flask import Blueprint

bp = Blueprint('main', __name__)

from GOOD.main import routes