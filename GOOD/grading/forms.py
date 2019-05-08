from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, TextAreaField, SelectMultipleField
from wtforms.validators import DataRequired, NumberRange
from GOOD.models import Discipline, Dancer, Couple


class CreateAdjudicatorForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    adjudicator_submit = SubmitField('Create adjudicator')


class DefaultDisciplinesDancesForm(FlaskForm):
    default_dd_submit = SubmitField('Create defaults')


class DisciplineForm(FlaskForm):
    discipline_name = StringField('Name', validators=[DataRequired()], description="Usually Standard or Latin")
    discipline_submit = SubmitField('Create Discipline')


class DanceForm(FlaskForm):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.discipline.choices = [(None, "Please select a discipline")] + \
                                  [(d.name, d.name) for d in Discipline.query.all()]

    dance_name = StringField('Name', validators=[DataRequired()], description="Slow Waltz, Tango, etc.")
    dance_tag = StringField('Tag', validators=[DataRequired()], description="SW, TG, etc.")
    discipline = SelectField('Discipline', validators=[DataRequired()], choices=[(None, "Please select a discipline")])
    dance_submit = SubmitField('Create Dance')


class DefaultLevelsForm(FlaskForm):
    default_level_submit = SubmitField('Create defaults')


class LevelForm(FlaskForm):
    level_name = StringField('Name', validators=[DataRequired()], description="D level, C level, Bronze, etc.")
    level_submit = SubmitField('Create Level')


class DancerForm(FlaskForm):
    dancer_name = StringField('Name', validators=[DataRequired()])
    dancer_submit = SubmitField('Add dancer')


class MultipleDancersForm(FlaskForm):
    multiple_dancers_names = TextAreaField(label="Names", validators=[DataRequired()],
                                           description="Excel/Sheets list of names to add.",
                                           render_kw={"style": "resize:none", "rows": "12"})
    multiple_dancers_submit = SubmitField('Add list of dancers')


class MultipleCouplesForm(FlaskForm):
    multiple_couples_names = TextAreaField(label="Couples", validators=[DataRequired()],
                                           description="CSV list (number,lead,follow) of couples to add.",
                                           render_kw={"style": "resize:none", "rows": "12"})
    multiple_couples_submit = SubmitField('Add list of couples')


class NewCoupleForm(FlaskForm):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        numbers = [c.number for c in Couple.query.all()]
        dancers = Dancer.query.order_by(Dancer.name).all()
        self.number.choices = [(i, i) for i in range(1, 101+len(numbers)) if i not in numbers]
        self.lead.choices = [(0, "Please select a lead")] + [(d.dancer_id, d.name) for d in dancers]
        self.follow.choices = [(0, "Please select a follow")] + [(d.dancer_id, d.name) for d in dancers]

    number = SelectField('Number', validators=[NumberRange(min=1, message="Please select a number")], coerce=int)
    lead = SelectField('Lead', validators=[NumberRange(min=1, message="Please select a lead")], coerce=int)
    follow = SelectField('Follow', validators=[NumberRange(min=1, message="Please select a follow")], coerce=int)
    submit = SubmitField('Add Couple')


class CoupleHeatForm(FlaskForm):
    def __init__(self, lvl, **kwargs):
        super().__init__(**kwargs)
        self.couple.choices = [(c.couple_id, c) for c in Couple.query.order_by(Couple.number).all()]
        self.heat.choices = [(0, "Please select a heat")] + \
                            [(h.heat_id, h) for h in sorted(lvl.heats, key=lambda x: (x.discipline_id, x.number))]

    couple = SelectMultipleField('Couples', coerce=int, render_kw={"size": "8"})
    heat = SelectField('Heat', validators=[NumberRange(min=1, message="Please select a heat")], coerce=int)
    submit = SubmitField('Add couple')
