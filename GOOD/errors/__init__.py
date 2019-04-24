from flask import Blueprint

bp = Blueprint('errors', __name__)

from GOOD.errors import handlers
