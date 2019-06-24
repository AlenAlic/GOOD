from GOOD import db, login
from flask import url_for, redirect, flash
from flask_login import UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from GOOD.values import *


def requires_access_level(access_levels):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.access not in access_levels:
                flash("Page inaccessible.")
                return redirect(url_for('main.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@login.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = 'user'
    user_id = db.Column(db.Integer, primary_key=True, nullable=False)
    username = db.Column(db.String(64), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, nullable=False, default=False)
    password_hash = db.Column(db.String(128), nullable=False)
    access = db.Column(db.Integer, index=True, nullable=False)
    discipline_id = db.Column(db.Integer, nullable=False, default=0)
    level_id = db.Column(db.Integer, nullable=False, default=0)
    order = db.Column(db.Integer, nullable=True, default=None)
    start_page = db.Column(db.Boolean, nullable=False, default=False)

    def get_id(self):
        return self.user_id

    def __repr__(self):
        return '{}'.format(self.username)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.access == ACCESS[ADMIN]

    def is_adjudicator(self):
        return self.access == ACCESS[ADJUDICATOR]

    def adjudicator_location(self):
        if self.start_page:
            return "{} is currently logged in at the home page.".format(self.username)
        disc = Discipline.query.filter(Discipline.discipline_id == self.discipline_id).first()
        lvl = Level.query.filter(Level.level_id == self.level_id).first()
        heat = GradingHeat.query.join(Heat) \
            .filter(Heat.discipline == disc, Heat.level == lvl, GradingHeat.order == self.order).first()
        if heat is not None:
            return "{adj} is currently grading Heat {number} {dance}, for the {disc} {lvl} level."\
                .format(adj=self.username, dance=heat.dance, number=heat.heat.number, lvl=heat.heat.level,
                        disc=heat.heat.discipline)
        elif self.discipline_id > 0 and self.level_id > 0:
            return "{adj} is currently at the selection page for the {disc} {lvl} level."\
                .format(adj=self.username, disc=disc, lvl=lvl)
        return "{} is currently not logged in.".format(self.username)


class Discipline(db.Model):
    __tablename__ = 'discipline'
    discipline_id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(64), unique=True, nullable=False)
    dances = db.relationship("Dance", back_populates="discipline", cascade='all, delete, delete-orphan')
    heats = db.relationship("Heat", back_populates="discipline", cascade='all, delete, delete-orphan')

    def __repr__(self):
        return '{}'.format(self.name)

    def adjudicating_discipline(self, adjudicator):
        heats = GradingHeat.query.all()
        heats = [h for h in heats if h.heat.discipline == self and h.adjudicating_heat(adjudicator)]
        return len(heats) > 0


class Dance(db.Model):
    __tablename__ = 'dance'
    dance_id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(64), unique=True, nullable=False)
    tag = db.Column(db.String(6), unique=True, nullable=False)
    discipline_id = db.Column(db.Integer, db.ForeignKey('discipline.discipline_id',
                                                        onupdate="CASCADE", ondelete="CASCADE"))
    discipline = db.relationship("Discipline", back_populates="dances")

    def __repr__(self):
        return '{}'.format(self.name)


class Level(db.Model):
    __tablename__ = 'level'
    level_id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(64), unique=True, nullable=False)
    heats = db.relationship("Heat", back_populates="level", cascade='all, delete, delete-orphan')

    def __repr__(self):
        return '{}'.format(self.name)

    def dancers(self, disc=None):
        d = []
        for h in self.disc_heat(disc):
            d.extend([c.lead for c in h.couples])
            d.extend([c.follow for c in h.couples])
        return d

    def couples(self, disc=None):
        c = []
        for h in self.disc_heat(disc):
            c.extend([c for c in h.couples])
        return c

    def disc_heat(self, disc=None):
        return self.heats if disc is None else [h for h in self.heats if h.discipline == disc]

    def disc_grading_heat(self, disc=None):
        heats = []
        for h in self.disc_heat(disc):
            heats.extend(h.grading_heats)
        return heats


class Dancer(db.Model):
    __tablename__ = 'dancer'
    dancer_id = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(160), unique=True, nullable=False)
    couples_lead = db.relationship("Couple", foreign_keys="Couple.lead_id", back_populates="lead",
                                   cascade='all, delete, delete-orphan')
    couples_follow = db.relationship("Couple", foreign_keys="Couple.follow_id", back_populates="follow",
                                     cascade='all, delete, delete-orphan')

    def __repr__(self):
        return '{}'.format(self.name)


heat_couple_table = db.Table(
    'heat_couple', db.Model.metadata,
    db.Column('heat_id', db.Integer, db.ForeignKey('heat.heat_id', onupdate="CASCADE", ondelete="CASCADE")),
    db.Column('couple_id', db.Integer, db.ForeignKey('couple.couple_id', onupdate="CASCADE", ondelete="CASCADE")),
    db.UniqueConstraint('heat_id', 'couple_id', name='_heat_couple_uc')
)


class Couple(db.Model):
    __tablename__ = 'couple'
    __table_args__ = (db.UniqueConstraint('lead_id', 'follow_id', name='_lead_follow_uc'),)
    couple_id = db.Column(db.Integer, primary_key=True, nullable=False)
    number = db.Column(db.Integer, nullable=False)
    lead_id = db.Column(db.Integer, db.ForeignKey('dancer.dancer_id', onupdate="CASCADE", ondelete="CASCADE"))
    lead = db.relationship("Dancer", back_populates="couples_lead", foreign_keys="Couple.lead_id")
    follow_id = db.Column(db.Integer, db.ForeignKey('dancer.dancer_id', onupdate="CASCADE", ondelete="CASCADE"))
    follow = db.relationship("Dancer",  back_populates="couples_follow", foreign_keys="Couple.follow_id")
    heats = db.relationship("Heat", secondary=heat_couple_table)
    grades = db.relationship("Grade", back_populates="couple", cascade='all, delete, delete-orphan')

    def __repr__(self):
        return '{number} - {lead} & {follow}'.format(number=self.number, lead=self.lead, follow=self.follow)

    def specific_grades(self, disc=None, lvl=None):
        return [g for g in self.grades if g.grading_heat.heat.discipline == disc and g.grading_heat.heat.level == lvl]


class Heat(db.Model):
    __tablename__ = 'heat'
    heat_id = db.Column(db.Integer, primary_key=True, nullable=False)
    number = db.Column(db.Integer, nullable=False)
    level_id = db.Column(db.Integer, db.ForeignKey('level.level_id', onupdate="CASCADE", ondelete="CASCADE"))
    level = db.relationship("Level", back_populates="heats")
    couples = db.relationship("Couple", secondary=heat_couple_table)
    discipline_id = db.Column(db.Integer, db.ForeignKey('discipline.discipline_id',
                                                        onupdate="CASCADE", ondelete="CASCADE"))
    discipline = db.relationship("Discipline", back_populates="heats")
    grading_heats = db.relationship("GradingHeat", back_populates="heat", cascade='all, delete, delete-orphan')

    def __repr__(self):
        return 'Heat {number} - {level} ({disc})'.format(number=self.number, level=self.level.name,
                                                         disc=self.discipline)

    def grading_heats_dance(self, dance=None):
        return self.grading_heats if dance is None else [h for h in self.grading_heats if h.dance == dance]

    def dancers(self):
        dancers = []
        for couple in self.couples:
            dancers.append(couple.lead)
            dancers.append(couple.follow)
        return dancers


class GradingHeat(db.Model):
    __tablename__ = 'grading_heat'
    grading_heat_id = db.Column(db.Integer, primary_key=True, nullable=False)
    heat_id = db.Column(db.Integer, db.ForeignKey('heat.heat_id', onupdate="CASCADE", ondelete="CASCADE"))
    heat = db.relationship("Heat", back_populates="grading_heats")
    dance_id = db.Column(db.Integer, db.ForeignKey('dance.dance_id', onupdate="CASCADE", ondelete="CASCADE"))
    dance = db.relationship("Dance")
    order = db.Column(db.Integer, nullable=False, default=0)
    grades = db.relationship("Grade", back_populates="grading_heat", cascade='all, delete, delete-orphan')

    def __repr__(self):
        return 'Grading{heat} - {dance}'.format(heat=self.heat, dance=self.dance)

    def display_name(self, short=True):
        if self.dance.name in DANCES_TAGS and short:
            return '{dance} - Heat {number}'.format(number=self.heat.number, dance=DANCES_TAGS[self.dance.name])
        else:
            return '{dance} - Heat {number}'.format(number=self.heat.number, dance=self.dance)

    def couples(self):
        return sorted(set([grade.couple for grade in self.grades]), key=lambda x: x.number)

    def adjudicator_grades(self, adjudicator=None):
        grades_list = {adj: [grade for grade in self.grades if grade.adjudicator == adj] for adj
                       in set([grade.adjudicator for grade in self.grades])}
        if adjudicator is not None:
            return grades_list[adjudicator]
        else:
            try:
                return list(grades_list.values())[0]
            except IndexError:
                return list()

    def adjudicating_heat(self, adjudicator):
        return len([grade for grade in self.grades if grade.adjudicator == adjudicator]) > 0


class Grade(db.Model):
    __tablename__ = 'grade'
    grading_id = db.Column(db.Integer, primary_key=True)
    couple_id = db.Column(db.Integer, db.ForeignKey('couple.couple_id', onupdate="CASCADE", ondelete="CASCADE"))
    couple = db.relationship("Couple", back_populates="grades")
    grading_heat_id = db.Column(db.Integer, db.ForeignKey('grading_heat.grading_heat_id',
                                                          onupdate="CASCADE", ondelete="CASCADE"))
    grading_heat = db.relationship("GradingHeat", back_populates="grades")
    lead_diploma = db.Column(db.Boolean, nullable=False, default=True)
    lead_grade = db.Column(db.Integer, nullable=False, default=0)
    follow_diploma = db.Column(db.Boolean, nullable=False, default=True)
    follow_grade = db.Column(db.Integer, nullable=False, default=0)
    adjudicator_id = db.Column(db.Integer, db.ForeignKey('user.user_id', onupdate="CASCADE", ondelete="CASCADE"))
    adjudicator = db.relationship("User")

    def __repr__(self):
        return 'Grade {grading_heat} - {dance} - {couple} - {adj}'.format(grading_heat=self.grading_heat,
                                                                          dance=self.grading_heat.dance,
                                                                          couple=self.couple, adj=self.adjudicator)
