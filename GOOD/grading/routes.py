from flask import render_template, request, redirect, url_for, flash, json, jsonify, g, current_app
from flask_login import login_required, current_user
from GOOD.grading import bp
from GOOD import db
from GOOD.models import requires_access_level, User, Discipline, Dance, Level, Dancer, Heat, Couple, GradingHeat, Grade
from GOOD.grading.forms import CreateAdjudicatorForm, DefaultDisciplinesDancesForm, DisciplineForm, DanceForm, \
    DefaultLevelsForm, LevelForm, DancerForm, MultipleDancersForm, NewCoupleForm, CoupleHeatForm, MultipleCouplesForm, \
    CoupleGradingHeatForm
from GOOD.values import *
from sqlalchemy import or_
from statistics import mean
from random import randint


DEFAULT_LEVEL_HEATS = {D_LEVEL: 3, C_LEVEL: 2, B_LEVEL: 2, A_LEVEL: 3}
DEFAULT_HEAT_OCCUPATION = {D_LEVEL: 7, C_LEVEL: 7, B_LEVEL: 6, A_LEVEL: 4}
TOTAL_COUPLES = sum(DEFAULT_LEVEL_HEATS[lvl] * DEFAULT_HEAT_OCCUPATION[lvl] for lvl in LEVELS)


def create_default_adjudicators():
    for a in ['Alice', 'Bob']:
        u = User()
        u.username = a
        u.set_password(a)
        u.is_active = True
        u.access = ACCESS[ADJUDICATOR]
        db.session.add(u)
        db.session.commit()


def create_default_disciplines_dances():
    standard = Discipline(name=STANDARD)
    db.session.add(standard)
    db.session.commit()
    latin = Discipline(name=LATIN)
    db.session.add(latin)
    db.session.commit()
    for d in STANDARD_DANCES:
        db.session.add(Dance(name=d, tag=DANCES_TAGS[d], discipline=standard))
    for d in LATIN_DANCES:
        db.session.add(Dance(name=d, tag=DANCES_TAGS[d], discipline=latin))
    db.session.commit()


def create_default_levels():
    db.session.add(Level(name=D_LEVEL))
    db.session.add(Level(name=C_LEVEL))
    db.session.add(Level(name=B_LEVEL))
    db.session.add(Level(name=A_LEVEL))
    db.session.commit()


def create_default_dancers():
    for d in DANCERS:
        db.session.add(Dancer(name=d))
    db.session.commit()


def create_default_heats():
    all_levels = Level.query.order_by(Level.level_id).all()
    all_disciplines = Discipline.query.order_by(Discipline.discipline_id).all()
    for lvl in all_levels:
        for disc in all_disciplines:
            for i in range(1, DEFAULT_LEVEL_HEATS[lvl.name]+1):
                heat = Heat(number=i, level=lvl, discipline=disc)
                lvl.heats.append(heat)
    db.session.commit()


def create_default_couples():
    all_dancers = Dancer.query.order_by(Dancer.dancer_id).all()
    for number, i in enumerate(range(0, TOTAL_COUPLES*2, 2)):
        db.session.add(Couple(number=number+1, lead=all_dancers[i], follow=all_dancers[i+1]))
    db.session.commit()


def assign_default_couples():
    all_couples = Couple.query.all()
    all_heats = Heat.query.order_by(Heat.heat_id).all()
    all_disciplines = Discipline.query.order_by(Discipline.discipline_id).all()
    for disc in all_disciplines:
        heats = [h for h in all_heats if h.discipline == disc]
        heat_count = 0
        for i in range(TOTAL_COUPLES):
            if heat_count < len(heats):
                heats[heat_count].couples.append(all_couples[i])
                if len(heats[heat_count].couples) >= DEFAULT_HEAT_OCCUPATION[heats[heat_count].level.name]:
                    heat_count += 1
    db.session.commit()


def reset_data():
    User.query.filter(User.access == ACCESS[ADJUDICATOR]).delete()
    Discipline.query.delete()
    Level.query.delete()
    Dancer.query.delete()
    db.session.commit()


@bp.route('/adjudicators', methods=['GET', 'POST'])
@login_required
@requires_access_level([ACCESS[ADMIN]])
def adjudicators():
    form = CreateAdjudicatorForm()
    if request.method == 'POST':
        if form.adjudicator_submit.name in request.form:
            if form.validate_on_submit():
                check_adjudicator = User.query\
                    .filter(User.access == ACCESS[ADJUDICATOR], User.username == form.username.data).first()
                if check_adjudicator is None:
                    u = User()
                    u.username = form.username.data
                    u.set_password(form.username.data)
                    u.is_active = True
                    u.access = ACCESS[ADJUDICATOR]
                    db.session.add(u)
                    db.session.commit()
                    flash("Added {name} as an adjudicator, with {name} as username and password."
                          .format(name=form.username.data), "success")
                else:
                    flash("{} is already an adjudicator in the system.".format(form.username.data))
                return redirect(url_for("grading.adjudicators"))
        if "delete_adjudicator" in request.form:
            adj = User.query.filter(User.user_id == request.form["delete_adjudicator"],
                                    User.access == ACCESS[ADJUDICATOR]).first()
            if adj is not None:
                flash("Removed {} from system as an adjudicator.".format(adj))
                db.session.delete(adj)
                db.session.commit()
                return redirect(url_for('grading.adjudicators'))
    all_adjudicators = User.query.filter(User.access == ACCESS[ADJUDICATOR]).all()
    return render_template('grading/adjudicators.html', form=form, all_adjudicators=all_adjudicators)


@bp.route('/disciplines_dances', methods=['GET', 'POST'])
@login_required
@requires_access_level([ACCESS[ADMIN]])
def disciplines_dances():
    all_disciplines = Discipline.query.order_by(Discipline.discipline_id).all()
    all_dances = Dance.query.order_by(Dance.dance_id).all()
    default_dd_form = DefaultDisciplinesDancesForm()
    discipline_form = DisciplineForm()
    dance_form = DanceForm()
    if request.method == 'POST':
        if default_dd_form.default_dd_submit.name in request.form:
            if default_dd_form.validate_on_submit():
                if len(all_disciplines) == 0 and len(all_dances) == 0:
                    create_default_disciplines_dances()
                    flash("Added default disciplines and dances.")
                    return redirect(url_for('grading.disciplines_dances'))
                else:
                    flash("Cannot create default disciplines and dances, there already are disciplines and/or dances "
                          "in the system.", "warning")
        if discipline_form.discipline_submit.name in request.form:
            if discipline_form.validate_on_submit():
                check = Discipline.query.filter(Discipline.name == discipline_form.discipline_name.data).first()
                if check is None:
                    d = Discipline()
                    d.name = discipline_form.discipline_name.data
                    db.session.add(d)
                    db.session.commit()
                    flash("Created {} discipline.".format(d.name), "success")
                    return redirect(url_for('grading.disciplines_dances'))
                else:
                    flash("Cannot create {} discipline, a discipline with that name already exists."
                          .format(dance_form.dance_name.data), "warning")
        if dance_form.dance_submit.name in request.form:
            if dance_form.validate_on_submit():
                check = Dance.query.filter(or_(Dance.name == dance_form.dance_name.data,
                                               Dance.tag == dance_form.dance_tag.data)).first()
                if check is None:
                    d = Dance()
                    d.name = dance_form.dance_name.data
                    d.tag = dance_form.dance_tag.data
                    d.discipline = Discipline.query.filter(Discipline.name == dance_form.discipline.data).first()
                    db.session.add(d)
                    db.session.commit()
                    flash("Created {} as a dance.".format(d.name), "success")
                    return redirect(url_for('grading.disciplines_dances'))
                else:
                    flash("Cannot create {} dance, a dance with that name or tag already exists."
                          .format(dance_form.dance_name.data), "warning")
        if "delete_discipline" in request.form:
            disc = Discipline.query.filter(Discipline.discipline_id == request.form["delete_discipline"]).first()
            if disc is not None:
                flash("Removed {} discipline from system, together with any dances associated with it.".format(disc))
                db.session.delete(disc)
                db.session.commit()
                return redirect(url_for('grading.disciplines_dances'))
        if "delete_dance" in request.form:
            dance = Dance.query.filter(Dance.dance_id == request.form["delete_dance"]).first()
            if dance is not None:
                flash("Removed {} dance from system.".format(dance))
                db.session.delete(dance)
                db.session.commit()
                return redirect(url_for('grading.disciplines_dances'))
    return render_template('grading/disciplines_dances.html', default_dd_form=default_dd_form,
                           discipline_form=discipline_form, dance_form=dance_form, all_disciplines=all_disciplines,
                           all_dances=all_dances)


@bp.route('/levels', methods=['GET', 'POST'])
@login_required
@requires_access_level([ACCESS[ADMIN]])
def levels():
    all_levels = Level.query.order_by(Level.level_id).all()
    default_level_form = DefaultLevelsForm()
    level_form = LevelForm()
    if request.method == 'POST':
        if default_level_form.default_level_submit.name in request.form:
            if default_level_form.validate_on_submit():
                if len(all_levels) == 0:
                    create_default_levels()
                    flash("Added default levels.")
                    return redirect(url_for('grading.levels'))
                else:
                    flash("Cannot create default levels, there already are levels in the system.", "warning")
        if level_form.level_submit.name in request.form:
            if level_form.validate_on_submit():
                check = Level.query.filter(Level.name == level_form.level_name.data).first()
                if check is None:
                    lvl = Level(name=level_form.level_name.data)
                    db.session.add(lvl)
                    db.session.commit()
                    flash("Created {} as a level.".format(lvl.name), "success")
                    return redirect(url_for('grading.levels'))
                else:
                    flash("Cannot create {} as a level, a level with that name already exists."
                          .format(level_form.level_name.data), "warning")
        if "delete_level" in request.form:
            lvl = Level.query.filter(Level.level_id == request.form["delete_level"]).first()
            if lvl is not None:
                flash("Removed {} level from system.".format(lvl))
                db.session.delete(lvl)
                db.session.commit()
                return redirect(url_for('grading.levels'))
    return render_template('grading/levels.html', default_level_form=default_level_form, level_form=level_form,
                           all_levels=all_levels)


@bp.route('/dancers', methods=['GET', 'POST'])
@login_required
@requires_access_level([ACCESS[ADMIN]])
def dancers():
    all_dancers = Dancer.query.order_by(Dancer.name).all()
    multiple_dancers_form = MultipleDancersForm()
    dancer_form = DancerForm()
    if request.method == 'POST':
        if multiple_dancers_form.multiple_dancers_submit.name in request.form:
            if multiple_dancers_form.validate_on_submit():
                import_list = multiple_dancers_form.multiple_dancers_names.data.split('\r\n')
                counter = {'success': 0, 'duplicates': 0, 'error': 0}
                for dancer_name in import_list:
                    dancer_name = dancer_name.split(",")[0].strip()
                    if len(dancer_name) >= 3:
                        check = Dancer.query.filter(Dancer.name == dancer_name).first()
                        if check is None:
                            db.session.add(Dancer(name=dancer_name))
                            db.session.commit()
                            counter['success'] += 1
                        else:
                            counter['duplicates'] += 1
                    else:
                        counter['error'] += 1
                if counter['success'] > 0:
                    flash("Imported {} new dancer(s) successfully.".format(counter['success']))
                else:
                    flash("No new dancers were imported.")
                if counter['duplicates'] > 0:
                    flash("{} duplicate name(s) ignored.".format(counter['duplicates']), "warning")
                if counter['error'] > 0:
                    flash("{} erroneous line(s) ignored.".format(counter['error']), "warning")
                return redirect(url_for("grading.dancers"))
        if dancer_form.dancer_submit.name in request.form:
            if dancer_form.validate_on_submit():
                check = Dancer.query.filter(Dancer.name == dancer_form.dancer_name.data).first()
                if check is None:
                    db.session.add(Dancer(name=dancer_form.dancer_name.data))
                    db.session.commit()
                    flash("Imported {} successfully.".format(dancer_form.dancer_name.data))
                    return redirect(url_for("grading.dancers"))
                else:
                    flash("Cannot add {}, he/she is already in the system.".format(dancer_form.dancer_name.data),
                          "warning")
        if "delete_dancer" in request.form:
            dancer = Dancer.query.filter(Dancer.dancer_id == request.form["delete_dancer"]).first()
            if dancer is not None:
                flash("Removed {} from system as a dancer.".format(dancer))
                db.session.delete(dancer)
                db.session.commit()
                return redirect(url_for('grading.dancers'))
    return render_template('grading/dancers.html', dancer_form=dancer_form, multiple_dancers_form=multiple_dancers_form,
                           all_dancers=all_dancers)


@bp.route('/couples', methods=['GET', 'POST'])
@login_required
@requires_access_level([ACCESS[ADMIN]])
def couples():
    all_couples = Couple.query.order_by(Couple.number).all()
    new_couple_form = NewCoupleForm()
    multiple_couples_form = MultipleCouplesForm()
    if request.method == 'POST':
        if multiple_couples_form.multiple_couples_submit.name in request.form:
            if multiple_couples_form.validate_on_submit():
                import_list = multiple_couples_form.multiple_couples_names.data.split('\r\n')
                counter = {'success': 0, 'duplicates': 0, 'dancers': 0, 'error': 0}
                couple_numbers = [c.number for c in Couple.query.all()]
                for couple in import_list:
                    couple_data = couple.split(",")
                    for i, item in enumerate(couple_data):
                        couple_data[i] = item.strip()
                    if len(couple_data) == 3:
                        try:
                            couple_data[0] = int(couple_data[0])
                            if int(couple_data[0]) not in couple_numbers:
                                check_lead = Dancer.query.filter(Dancer.name == couple_data[1]).first()
                                check_follow = Dancer.query.filter(Dancer.name == couple_data[2]).first()
                                if check_lead is not None and check_follow is not None:
                                    check = Couple.query.filter(Couple.lead == check_lead,
                                                                Couple.follow == check_follow) \
                                        .first()
                                    if check is None:
                                        db.session.add(
                                            Couple(number=couple_data[0], lead=check_lead, follow=check_follow))
                                        db.session.commit()
                                        counter['success'] += 1
                                    else:
                                        counter['duplicates'] += 1
                                else:
                                    counter['dancers'] += 1
                            else:
                                counter['duplicates'] += 1
                        except ValueError:
                            counter['error'] += 1
                    else:
                        counter['error'] += 1
                if counter['success'] > 0:
                    flash("Imported {} new couple(s) successfully.".format(counter['success']))
                else:
                    flash("No new couples were imported.")
                if counter['duplicates'] > 0:
                    flash("{} duplicate number(s) ignored.".format(counter['duplicates']), "warning")
                if counter['dancers'] > 0:
                    flash("Could not create {} couple(s), due to one of the dancers not being in the system."
                          .format(counter['dancers']), "warning")
                if counter['error'] > 0:
                    flash("{} row(s) ignored due to not being a CSV of the correct format."
                          .format(counter['error']), "warning")
                return redirect(url_for("grading.couples"))
        if new_couple_form.submit.name in request.form:
            if new_couple_form.validate_on_submit():
                check_lead = Dancer.query.filter(Dancer.dancer_id == new_couple_form.lead.data).first()
                check_follow = Dancer.query.filter(Dancer.dancer_id == new_couple_form.follow.data).first()
                check_couple = Couple.query.filter(Couple.lead == check_lead, Couple.follow == check_follow).first()
                if check_lead == check_follow:
                    flash("{} cannot dance with him-/herself.".format(check_lead))
                elif check_couple is not None:
                    flash("{lead} and {follow} are already a couple (number {number})."
                          .format(lead=check_lead, follow=check_follow, number=check_couple.number))
                else:
                    couple = Couple()
                    couple.number = new_couple_form.number.data
                    couple.lead = Dancer.query.filter(Dancer.dancer_id == new_couple_form.lead.data).first()
                    couple.follow = Dancer.query.filter(Dancer.dancer_id == new_couple_form.follow.data).first()
                    db.session.add(couple)
                    db.session.commit()
                    flash("Added {lead} (lead) and {follow} (follow) as a couple to system."
                          .format(lead=couple.lead, follow=couple.follow))
                return redirect(url_for('grading.couples'))
        if "delete_couple" in request.form:
            couple = Couple.query.filter(Couple.couple_id == request.form["delete_couple"]).first()
            if couple is not None:
                flash("Removed {lead} (lead) and {follow} (follow) as a couple from system."
                      .format(lead=couple.lead, follow=couple.follow))
                db.session.delete(couple)
                db.session.commit()
                return redirect(url_for('grading.couples'))
    return render_template('grading/couples.html', new_couple_form=new_couple_form,
                           multiple_couples_form=multiple_couples_form, all_couples=all_couples)


@bp.route('/setup_levels', methods=['GET', 'POST'])
@login_required
@requires_access_level([ACCESS[ADMIN]])
def setup_levels():
    all_levels = Level.query.order_by(Level.level_id).all()
    if len(all_levels) == 0:
        flash('Please add at least one level first.')
        return redirect(url_for('grading.levels'))
    lvl = request.args.get('level_id', default=0, type=int)
    if lvl == 0 and len(all_levels) > 0:
        return redirect(url_for('grading.setup_levels', level_id=all_levels[0].level_id))
    lvl = Level.query.filter(Level.level_id == lvl).first()
    if lvl is None:
        return redirect(url_for('grading.setup_levels'))
    couple_heat_form = CoupleHeatForm(lvl)
    all_disciplines = Discipline.query.order_by(Discipline.discipline_id).all()
    if request.method == 'POST':
        if couple_heat_form.submit.name in request.form:
            if couple_heat_form.validate_on_submit():
                heat = Heat.query.filter(Heat.heat_id == couple_heat_form.heat.data).first()
                couples_list = Couple.query.filter(Couple.couple_id.in_(couple_heat_form.couple.data)).all()
                counter = {'success': 0, 'duplicates': 0}
                for couple in couples_list:
                    if couple in heat.couples:
                        flash("Couple {couple} is already dancing in Heat {number}, {disc} {level} level."
                              .format(couple=couple, number=heat.number, disc=heat.discipline, level=heat.level),
                              "warning")
                        counter["duplicates"] += 1
                    elif couple.lead in heat.dancers():
                        flash("{dancer} is already dancing in Heat {number}, {disc} {level} level."
                              .format(dancer=couple.lead, number=heat.number, disc=heat.discipline, level=heat.level),
                              "warning")
                    elif couple.follow in heat.dancers():
                        flash("{dancer} is already dancing in Heat {number}, {disc} {level} level."
                              .format(dancer=couple.follow, number=heat.number, disc=heat.discipline, level=heat.level),
                              "warning")
                    else:
                        couple.heats.append(heat)
                        db.session.add(couple)
                        db.session.commit()
                        counter["success"] += 1
                flash("Added {couples} couples to {heat}.".format(couples=counter["success"], heat=heat))
                return redirect(url_for('grading.setup_levels', level_id=lvl.level_id))
        if "change_heats" in request.form:
            for r in request.form:
                if r != "change_heats":
                    req = r.split('-')
                    disc = Discipline.query.filter(Discipline.discipline_id == req[1]).first()
                    if disc is not None:
                        if req[0] == "add_heat":
                            heat = Heat(number=len(lvl.disc_heat(disc))+1, level=lvl, discipline=disc)
                            lvl.heats.append(heat)
                            db.session.commit()
                            flash('Added {}'.format(heat))
                            return redirect(url_for('grading.setup_levels', level_id=lvl.level_id))
                        elif req[0] == "remove_heat":
                            if len(lvl.heats) > 0:
                                heat = lvl.disc_heat(disc)[-1]
                                db.session.delete(heat)
                                db.session.commit()
                                flash('Deleted {}'.format(heat))
                            else:
                                flash('There are no heats to delete from the {} level.'.format(lvl))
                            return redirect(url_for('grading.setup_levels', level_id=lvl.level_id))
                        else:
                            pass
    return render_template('grading/setup_levels.html', lvl=lvl, couple_heat_form=couple_heat_form,
                           all_disciplines=all_disciplines)


@bp.route('/remove_dancer_from_heat', methods=['DELETE'])
@login_required
@requires_access_level([ACCESS[ADMIN]])
def remove_dancer_from_heat():
    data = json.loads(request.data)
    heat = Heat.query.filter(Heat.heat_id == data["heatId"]).first()
    couple = Couple.query.filter(Couple.couple_id == data["coupleId"]).first()
    heat.couples.remove(couple)
    db.session.commit()
    return jsonify({"removed": couple not in heat.couples})


@bp.route('/manage_heats', methods=['GET', 'POST'])
@login_required
@requires_access_level([ACCESS[ADMIN]])
def manage_heats():
    couple_heat_form = CoupleGradingHeatForm()
    if request.method == 'POST':
        if "create_heats" in request.form:
            form = {k: v for k, v in request.form.items()}
            all_heats = Heat.query.order_by(Heat.heat_id).all()
            adjudicate = {adj: {disc: False for disc in g.all_disciplines} for adj in g.all_adjudicators}
            for adj in g.all_adjudicators:
                for disc in g.all_disciplines:
                    try:
                        _ = form["adjudicator-{adj_id}-discipline-{disc_id}".format(adj_id=adj.user_id,
                                                                                    disc_id=disc.discipline_id)]
                        adjudicate[adj][disc] = True
                    except KeyError:
                        pass
            order = 0
            for heat in all_heats:
                for dance in heat.discipline.dances:
                    try:
                        _ = form["heat-{heat_id}-dance-{dance_id}".format(heat_id=heat.heat_id,
                                                                          dance_id=dance.dance_id)]
                        grading_heat = GradingHeat(heat=heat, dance=dance, order=order)
                        order += 1
                        for adj in g.all_adjudicators:
                            if adjudicate[adj][heat.discipline]:
                                for couple in heat.couples:
                                    grade = Grade(grading_heat=grading_heat, couple=couple, adjudicator=adj)
                                    try:
                                        _ = form["heat-{heat_id}-lead-{couple_id}".format(heat_id=heat.heat_id,
                                                                                          couple_id=couple.couple_id)]
                                        grade.lead_diploma = True
                                        if current_app.config.get('DEBUG'):
                                            grade.lead_grade = randint(1, 10)
                                    except KeyError:
                                        grade.lead_diploma = False
                                    try:
                                        _ = form["heat-{heat_id}-follow-{couple_id}".format(heat_id=heat.heat_id,
                                                                                            couple_id=couple.couple_id)]
                                        grade.follow_diploma = True
                                        if current_app.config.get('DEBUG'):
                                            grade.follow_grade = randint(1, 10)
                                    except KeyError:
                                        grade.follow_diploma = False
                                    if grade.lead_diploma or grade.follow_diploma:
                                        grading_heat.grades.append(grade)
                    except KeyError:
                        pass
            db.session.commit()
            for disc in g.all_disciplines:
                for level in g.all_levels:
                    heats = GradingHeat.query.join(Heat).filter(Heat.level == level, Heat.discipline == disc).all()
                    heats = sorted(heats, key=lambda x: x.dance_id)
                    for count, item in enumerate(heats):
                        item.order = count
            db.session.commit()
            return redirect(url_for('grading.manage_heats'))
        if "delete_heats" in request.form:
            GradingHeat.query.delete()
            db.session.commit()
            return redirect(url_for('grading.manage_heats'))
        if couple_heat_form.submit.name in request.form:
            if couple_heat_form.validate_on_submit():
                couple = Couple.query.filter(Couple.couple_id == couple_heat_form.couple.data).first()
                for h in couple_heat_form.heat.data:
                    heat = GradingHeat.query.filter(GradingHeat.grading_heat_id == h).first()
                    check_grades = Grade.query.filter(Grade.grading_heat == heat, Grade.couple == couple).all()
                    if len(check_grades) == 0:
                        for adj in g.all_adjudicators:
                            db.session.add(Grade(couple=couple, grading_heat=heat, adjudicator=adj,
                                                 lead_diploma=couple_heat_form.lead_diploma.data,
                                                 follow_diploma=couple_heat_form.follow_diploma.data))
                        if couple not in heat.heat.couples:
                            heat.heat.couples.append(couple)
                        db.session.commit()
                        flash('Added {couple} to Heat {number} ({dance}) in the {disc} {lvl} level.'
                              .format(couple=couple, disc=heat.heat.discipline, lvl=heat.heat.level,
                                      number=heat.heat.number, dance=heat.dance))
                    else:
                        flash('Couple {couple} is already dancing in Heat {number} ({dance}) in the {disc} {lvl} level.'
                              .format(couple=couple, disc=heat.heat.discipline, lvl=heat.heat.level,
                                      number=heat.heat.number,
                                      dance=heat.dance))
                return redirect(url_for('grading.manage_heats'))
    return render_template('grading/manage_heats.html', couple_heat_form=couple_heat_form)


@bp.route('/change_grading_heat_order', methods=['PATCH'])
@login_required
@requires_access_level([ACCESS[ADMIN]])
def change_grading_heat_order():
    data = json.loads(request.data)
    heats = GradingHeat.query.filter(GradingHeat.grading_heat_id.in_(data["gradingHeatIds"])).all()
    for heat in heats:
        heat.order = data["gradingHeatIds"]["{}".format(heat.grading_heat_id)]
    db.session.commit()
    return jsonify({"data": True})


@bp.route('/remove_grade_from_grading_heat', methods=['DELETE'])
@login_required
@requires_access_level([ACCESS[ADMIN]])
def remove_grade_from_grading_heat():
    data = json.loads(request.data)
    grading_heat = GradingHeat.query.filter(GradingHeat.grading_heat_id == data["gradingHeatId"]).first()
    couple = Couple.query.filter(Couple.couple_id == data["coupleId"]).first()
    grades = Grade.query.filter(Grade.couple == couple, Grade.grading_heat == grading_heat).all()
    for grade in grades:
        db.session.delete(grade)
    heat_couples = set([c for h in grading_heat.heat.grading_heats for c in h.couples()])
    if couple not in heat_couples and couple in grading_heat.heat.couples:
        grading_heat.heat.couples.remove(couple)
    db.session.commit()
    return jsonify({
        "removed": len(Grade.query.filter(Grade.couple == couple, Grade.grading_heat == grading_heat).all()) == 0,
        "message": "Removed couple {couple} from {dance} Heat {number}, "
                   "{lvl} level, {disc}.".format(couple=couple, dance=grading_heat.dance,
                                                 number=grading_heat.heat.number, lvl=grading_heat.heat.level,
                                                 disc=grading_heat.heat.discipline)
    })


@bp.route('/change_diploma', methods=['PATCH'])
@login_required
@requires_access_level([ACCESS[ADMIN]])
def change_diploma():
    data = json.loads(request.data)
    grade = Grade.query.filter(Grade.grading_id == data["gradeId"]).first()
    diploma = not data["diploma"]
    if data["role"] == "lead":
        grade.lead_diploma = diploma
        dancer = grade.couple.lead
    else:
        grade.follow_diploma = diploma
        dancer = grade.couple.follow
    db.session.commit()
    if diploma:
        message = "{dancer} will get graded on the {dance} {lvl} level."\
            .format(dancer=dancer, dance=grade.grading_heat.dance, lvl=grade.grading_heat.heat.level)
    else:
        message = "{dancer} will not get graded on the {dance} {lvl} level."\
            .format(dancer=dancer, dance=grade.grading_heat.dance, lvl=grade.grading_heat.heat.level)
    return jsonify({"diploma": diploma,  "message": message})


@bp.route('/print_heat_lists', methods=['GET'])
@login_required
@requires_access_level([ACCESS[ADMIN]])
def print_heat_lists():
    print_list = {disc: {lvl: None for lvl in g.all_levels} for disc in g.all_disciplines}
    for disc in g.all_disciplines:
        for lvl in g.all_levels:
            print_list[disc][lvl] = GradingHeat.query.join(Heat)\
                .filter(Heat.discipline == disc, Heat.level == lvl).order_by(GradingHeat.order).all()
    all_couples = sorted(g.all_couples, key=lambda x: x.lead.name)
    return render_template('grading/print_heat_lists.html', print_list=print_list, all_couples=all_couples)


@bp.route('/live_grading', methods=['GET'])
@login_required
@requires_access_level([ACCESS[ADMIN]])
def live_grading():
    disc = Discipline.query.filter(Discipline.discipline_id == request.args.get('discipline_id', 0, int)).first()
    lvl = Level.query.filter(Level.level_id == request.args.get('level_id', 0, int)).first()
    order = request.args.get('order', 0, int)
    heats = GradingHeat.query.join(Heat).filter(Heat.discipline == disc, Heat.level == lvl) \
        .order_by(GradingHeat.order).all()
    grading_heat = GradingHeat.query.join(Heat)\
        .filter(Heat.discipline == disc, Heat.level == lvl, GradingHeat.order == order).first()
    adjudicators_list = {}
    if len(heats) > 0 and grading_heat is not None:
        adjudicators_list = {adj: sorted([grade for grade in grading_heat.grades if grade.adjudicator == adj],
                                         key=lambda x: x.couple.number) for adj
                             in sorted(set([grade.adjudicator for grade in grading_heat.grades]),
                                       key=lambda x: x.username)}
    zeros = {adj: [grade_item.follow_grade for grade_item in adjudicators_list[adj] if grade_item.follow_diploma] +
                  [grade_item.lead_grade for grade_item in adjudicators_list[adj] if grade_item.lead_diploma]
             for adj in adjudicators_list.keys()}
    grades_required = {adj: len(zeros[adj]) for adj in adjudicators_list.keys()}
    zeros = {adj: len(zeros[adj]) - zeros[adj].count(0) for adj in adjudicators_list.keys()}
    return render_template('grading/live_grading.html', heats=heats, grading_heat=grading_heat,
                           adjudicators_list=adjudicators_list, zeros=zeros, grades_required=grades_required)


@bp.route('/view_grades', methods=['GET'])
@login_required
@requires_access_level([ACCESS[ADMIN]])
def view_grades():
    disc = Discipline.query.filter(Discipline.discipline_id == request.args.get('discipline_id', 0, int)).first()
    lvl = Level.query.filter(Level.level_id == request.args.get('level_id', 0, int)).first()
    master_list = {}
    diplomas = 0
    graded = 0
    if lvl is not None and disc is not None:
        couple_list = lvl.couples(disc)
        grade_list = Grade.query.filter(Grade.couple_id.in_([c.couple_id for c in couple_list])).all()
        grade_list = [grade for grade in grade_list if grade.grading_heat.heat.discipline == disc
                      and grade.grading_heat.heat.level == lvl]
        adjudicators_list = set([grade.adjudicator for grade in grade_list])
        master_list = {couple: {} for couple in couple_list}
        for grade in grade_list:
            master_list[grade.couple][grade.grading_heat.dance] = {}
            master_list[grade.couple][grade.grading_heat.dance][FINAL_GRADE] = {}
            master_list[grade.couple][grade.grading_heat.dance][GRADE] = grade
            if grade.lead_diploma:
                master_list[grade.couple][grade.grading_heat.dance][FINAL_GRADE][LEAD] = 0
            if grade.follow_diploma:
                master_list[grade.couple][grade.grading_heat.dance][FINAL_GRADE][FOLLOW] = 0
        for grade in grade_list:
            master_list[grade.couple][grade.grading_heat.dance][grade.adjudicator] = {}
            if grade.lead_diploma:
                master_list[grade.couple][grade.grading_heat.dance][grade.adjudicator][LEAD] = grade.lead_grade
            if grade.follow_diploma:
                master_list[grade.couple][grade.grading_heat.dance][grade.adjudicator][FOLLOW] = grade.follow_grade
        for couple in master_list:
            for dance in master_list[couple]:
                for d in master_list[couple][dance][FINAL_GRADE]:
                    grades = [master_list[couple][dance][adj][d] for adj in adjudicators_list]
                    master_list[couple][dance][FINAL_GRADE][d] = round(mean(grades), 2)
        for couple in master_list:
            try:
                if all([master_list[couple][dance][GRADE].lead_diploma for dance in master_list[couple]]):
                    diplomas += 1
                if min([master_list[couple][dance][FINAL_GRADE][LEAD] for dance in master_list[couple]]) > 0:
                    graded += 1
            except (KeyError, ValueError):
                pass
            try:
                if all([master_list[couple][dance][GRADE].follow_diploma for dance in master_list[couple]]):
                    diplomas += 1
                if min([master_list[couple][dance][FINAL_GRADE][FOLLOW] for dance in master_list[couple]]) > 0:
                    graded += 1
            except (KeyError, ValueError):
                pass
        for couple in master_list:
            for dance in master_list[couple]:
                for d in master_list[couple][dance][FINAL_GRADE]:
                    master_list[couple][dance][FINAL_GRADE][d] = \
                        round(calculate_grade(master_list[couple][dance][FINAL_GRADE][d]), 2)
        if len(g.all_adjudicators) == 2:
            for couple in master_list:
                for dance in master_list[couple]:
                    for d in master_list[couple][dance][FINAL_GRADE]:
                        master_list[couple][dance][FINAL_GRADE][d] = \
                            fancy_grade(master_list[couple][dance][FINAL_GRADE][d])
        else:
            for couple in master_list:
                for dance in master_list[couple]:
                    for d in master_list[couple][dance][FINAL_GRADE]:
                        master_list[couple][dance][FINAL_GRADE][d] = \
                            formatted_grade(master_list[couple][dance][FINAL_GRADE][d])
    return render_template('grading/view_grades.html', master_list=master_list, level=lvl, discipline=disc,
                           diplomas=diplomas, graded=graded)


@bp.route('/reset', methods=['GET', 'POST'])
@login_required
@requires_access_level([ACCESS[ADMIN]])
def reset():
    if request.method == "POST":
        if "reset_system" in request.form:
            reset_data()
            meta = db.metadata
            for table in reversed(meta.sorted_tables):
                if table.name != 'user':
                    print('Table {} has been reset.'.format(table))
                    # noinspection SqlNoDataSourceInspection
                    db.session.execute("ALTER TABLE {} AUTO_INCREMENT = 1;".format(table.name))
            db.session.commit()
            flash("All tables have been reset.")
            return redirect(url_for('main.dashboard'))
    return render_template('grading/reset.html')


@bp.route('/adjudicate_start_page', methods=['GET'])
@login_required
@requires_access_level([ACCESS[ADJUDICATOR]])
def adjudicate_start_page():
    current_user.discipline_id = 0
    current_user.level_id = 0
    current_user.order = None
    current_user.start_page = True
    db.session.commit()
    return render_template('grading/adjudicate_start_page.html')


@bp.route('/adjudicate_level', methods=['GET'])
@login_required
@requires_access_level([ACCESS[ADJUDICATOR]])
def adjudicate_level():
    discipline_id = request.args.get('discipline_id', 0, int)
    level_id = request.args.get('level_id', 0, int)
    order = request.args.get('order')
    current_user.discipline_id = discipline_id
    current_user.level_id = level_id
    current_user.order = order
    current_user.start_page = False
    db.session.commit()
    disc = Discipline.query.filter(Discipline.discipline_id == discipline_id).first()
    lvl = Level.query.filter(Level.level_id == level_id).first()
    grading_heat = GradingHeat.query.join(Heat)\
        .filter(Heat.discipline == disc, Heat.level == lvl, GradingHeat.order == order).first()
    grades = []
    if grading_heat is not None:
        grades = Grade.query.join(GradingHeat).filter(GradingHeat.grading_heat_id == grading_heat.grading_heat_id,
                                                      Grade.adjudicator == current_user).all()
        grades = sorted(grades, key=lambda x: x.couple.number)
    heats = GradingHeat.query.join(Heat).filter(Heat.discipline == disc, Heat.level == lvl)\
        .order_by(GradingHeat.order).all()
    zeros = [grade_item.lead_grade for grade_item in grades if grade_item.lead_diploma] + \
            [grade_item.follow_grade for grade_item in grades if grade_item.follow_diploma]
    grades_required = len(zeros)
    zeros = len(zeros) - zeros.count(0)
    return render_template('grading/adjudicate_level.html', grading_heat=grading_heat, heats=heats, order=order,
                           grades=grades, zeros=zeros, grades_required=grades_required, level=lvl, discipline=disc)
