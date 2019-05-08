from flask_login import current_user
from flask_socketio import emit, disconnect
from .. import socketio
import functools
from GOOD import db
from GOOD.models import GradingHeat, Grade, User
from GOOD.values import calculate_grade


def authenticated_only(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            disconnect()
        else:
            return f(*args, **kwargs)
    return wrapped


@socketio.on('adjudicatorJoined')
@authenticated_only
def adjudicator_joined(message):
    adjudicator = User.query.filter(User.user_id == message["adjudicatorId"]).first()
    grading_heat = GradingHeat.query.filter(GradingHeat.grading_heat_id == message["gradingHeatId"]).first()
    data = {"message": "{adj} entered the {heat} - {level} level.".format(adj=adjudicator.username,
                                                                          heat=grading_heat.display_name(short=False),
                                                                          level=grading_heat.heat.level.name)}
    emit('notifyAdjudicatorJoined', data, broadcast=True)


@socketio.on('adjudicatorLeft')
@authenticated_only
def adjudicator_left(message):
    adjudicator = User.query.filter(User.user_id == message["adjudicatorId"]).first()
    grading_heat = GradingHeat.query.filter(GradingHeat.grading_heat_id == message["gradingHeatId"]).first()
    data = {"message": "{adj} left the {disc} {level} level.".format(adj=adjudicator.username,
                                                                     disc=grading_heat.heat.discipline.name,
                                                                     level=grading_heat.heat.level.name)}
    emit('notifyAdjudicatorLeft', data, broadcast=True)


@socketio.on('gradeGiven')
@authenticated_only
def grade_given(message):
    grade = Grade.query.filter(Grade.grading_id == message["gradeId"]).first()
    if message["role"] == "lead":
        grade.lead_grade = int(message["grade"])
    if message["role"] == "follow":
        grade.follow_grade = int(message["grade"])
    db.session.commit()
    grading_heat = GradingHeat.query.filter(GradingHeat.grading_heat_id == message["gradingHeatId"]).first()
    grades = Grade.query.join(GradingHeat).filter(GradingHeat.grading_heat_id == grading_heat.grading_heat_id,
                                                  Grade.adjudicator == current_user).all()
    zeros = [grade_item.lead_grade for grade_item in grades if grade_item.lead_diploma] + \
            [grade_item.follow_grade for grade_item in grades if grade_item.follow_diploma]
    data = {
        "gradeId": grade.grading_id,
        "grade": "{:2g}".format(calculate_grade(grade.lead_grade if message["role"] == "lead" else grade.follow_grade)),
        "role": message["role"],
        "graded": len(zeros) - zeros.count(0),
        "dancers": len(zeros),
        "adjudicatorId": str(current_user.user_id),
        "gradingHeatId": message["gradingHeatId"]
    }
    emit('updateGrade', data, broadcast=True)
