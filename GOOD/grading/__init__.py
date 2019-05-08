from flask import Blueprint

bp = Blueprint('grading', __name__)

from GOOD.grading import routes, events
