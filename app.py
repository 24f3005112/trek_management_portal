from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)


@app.template_filter('active_check')
def active_check(user_id):
    u = db.session.get(User, user_id)
    return u.is_active if u else False


app.secret_key = "secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trek.db'
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(60))
    is_active = db.Column(db.Boolean(), default=True)


class Trek(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trek_name = db.Column(db.String(60), nullable=False)
    trek_location = db.Column(db.String(60), nullable=False)
    trek_difficulty = db.Column(db.String(60), nullable=False)
    trek_id = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.String(60), nullable=False)
    total_slots = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    price = db.Column(db.String(60), nullable=False)
    max_altitude = db.Column(db.String(60), nullable=False)
    Description = db.Column(db.String(60), nullable=False)
    trek_status = db.Column(db.String(60), nullable=False)
    assigned_staff_id = db.Column(db.Integer, db.ForeignKey('staff.id'), nullable=False)


class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    Staff_Name = db.Column(db.String(60), nullable=False)
    staff_id = db.Column(db.Integer, nullable=False)
    contact_details = db.Column(db.String(60), nullable=False)
    staff_experience = db.Column(db.String(60), nullable=False)
    staff_rating = db.Column(db.String(60))
    is_approved = db.Column(db.Boolean(), default=False)


class Trekker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    Trekker_Name = db.Column(db.String(60), nullable=False)
    trek_history = db.Column(db.String(600), nullable=False)
    experience = db.Column(db.String(60), nullable=False)
    emergency_contact_name = db.Column(db.String(60), nullable=False)
    emergency_contact_phone = db.Column(db.String(60), nullable=False)
    medical_condition = db.Column(db.String(60), nullable=False)
    gender = db.Column(db.String(60), nullable=True)


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    trek_id = db.Column(db.Integer, db.ForeignKey('trek.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    booking_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(60), nullable=False)

    trek = db.relationship('Trek', backref=db.backref('bookings', lazy=True))
    user = db.relationship('User', backref=db.backref('bookings', lazy=True))


@app.route("/")
def index():
    if 'user_id' in session:
        role = session.get('role')
        if role == "trekker":
            return redirect(url_for('trekker_dashboard'))
        elif role == "staff":
            return redirect(url_for('staff_dashboard'))
        elif role == "admin":
            return redirect(url_for('admin_dashboard'))
        else:
            session.clear()
            return redirect(url_for('register'))
    return redirect(url_for('login'))


@app.route("/register", methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        fullname = request.form.get('name')
        contact_details = request.form.get('contact_details')

        if not email or not password or not role:
            flash("You forgot to fill something!")
            return redirect(url_for('register'))

        found = User.query.filter_by(email=email).first()
        if found:
            flash("That email is taken. Try again!")
            return redirect(url_for('register'))
        else:
            new_user = User(email=email, password=password, role=role, is_active=True)
            db.session.add(new_user)
            db.session.commit()

        if role == "trekker":
            trekker = Trekker(
                user_id=new_user.id,
                Trekker_Name=fullname,
                trek_history="None",
                experience="Beginner",
                emergency_contact_name="None",
                emergency_contact_phone="None",
                medical_condition="None",
                gender="None"
            )
            db.session.add(trekker)
            db.session.commit()
            flash("You have been registered successfully! Please login.")
            return redirect(url_for('login'))
        elif role == "staff":
            new_staff = Staff(
                user_id=new_user.id,
                Staff_Name=fullname,
                staff_id=int(datetime.utcnow().timestamp() % 10000),
                contact_details=contact_details if contact_details else "None",
                staff_experience='not declared',
                staff_rating='0.0',
                is_approved=False
            )
            db.session.add(new_staff)
            db.session.commit()
            flash('Registered successfully! Waiting for admin to approve ....')
            return redirect(url_for('login'))
    return render_template('register.html')


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if not user or user.password != password:
            flash("Invalid username or password")
            return redirect(url_for('login'))
        if not user.is_active:
            flash("This account has been deactivated")
            return redirect(url_for('login'))
        if user.role == 'staff':
            staff_profile = Staff.query.filter_by(user_id=user.id).first()
            if not staff_profile or not staff_profile.is_approved:
                flash('Dashboard access is currently denied. Admin approval is pending.')
                return redirect(url_for('login'))

        session['user_id'] = user.id
        session['email'] = user.email
        session['role'] = user.role
        return redirect(url_for('index'))
    return render_template('login.html')


@app.route("/logout")
def logout():
    session.clear()
    flash('You have been logged out')
    return redirect(url_for('login'))


@app.route('/admin_dashboard')
def admin_dashboard():
    if session.get('role') != 'admin':
        return "Unauthorized", 403
    total_treks = Trek.query.count()
    total_users_staffs = User.query.filter(User.role.in_(['trekker', 'staff'])).count()
    total_bookings = Booking.query.count()
    search_query = request.args.get('search_query', '').strip()
    if search_query:
        if search_query.isdigit():
            treks = Trek.query.filter(Trek.id == int(search_query)).all()
            staff_members = Staff.query.filter(
                (Staff.id == int(search_query)) | (Staff.staff_id == int(search_query))).all()
            users = User.query.filter((User.id == int(search_query)) & (User.role == 'trekker')).all()
        else:
            treks = Trek.query.filter(Trek.trek_name.contains(search_query)).all()
            staff_members = Staff.query.filter(Staff.Staff_Name.contains(search_query)).all()
            users = User.query.join(Trekker).filter(Trekker.Trekker_Name.contains(search_query)).all()
    else:
        treks = Trek.query.all()
        staff_members = Staff.query.all()
        users = User.query.filter_by(role='trekker').all()

    return render_template(
        'admin_dashboard.html',
        total_treks=total_treks,
        total_users_staffs=total_users_staffs,
        total_bookings=total_bookings,
        treks=treks,
        staff_members=staff_members,
        users=users
    )


@app.route('/admin_add_trek', methods=['GET', 'POST'])
def admin_add_trek():
    if session.get('role') != 'admin':
        return "Unauthorized", 403
    if request.method == 'POST':
        slots_input = int(request.form.get('available_slots'))
        new_trek = Trek(
            trek_name=request.form.get('trek_name'),
            trek_location=request.form.get('trek_location'),
            trek_difficulty=request.form.get('trek_difficulty'),
            duration=request.form.get('duration'),
            total_slots=slots_input,  # Force match original total capacity
            available_slots=slots_input,
            assigned_staff_id=int(request.form.get('assigned_staff_id')),
            trek_status=request.form.get('status') or request.form.get('trek_status'),
            price=request.form.get('price'),
            max_altitude=request.form.get('max_altitude'),
            Description=request.form.get('description'),
            start_date=datetime.strptime(request.form.get('start_date'), '%Y-%m-%d'),
            end_date=datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
        )
        new_trek.trek_id = int(datetime.utcnow().timestamp() % 10000)
        db.session.add(new_trek)
        db.session.commit()
        flash('Trek Document Added Successfully!')
        return redirect(url_for('admin_dashboard'))
    staff_list = Staff.query.filter_by(is_approved=True).all()
    return render_template('admin_add_trek.html', staff_list=staff_list)


@app.route('/admin_edit_trek/<int:id>', methods=['GET', 'POST'])
def admin_edit_trek(id):
    if session.get('role') != 'admin':
        return "Unauthorized", 403
    trek = Trek.query.get_or_404(id)
    if request.method == 'POST':
        # Align keys perfectly with template field name hooks
        trek.trek_name = request.form.get('name')
        trek.trek_location = request.form.get('location')
        trek.trek_difficulty = request.form.get('difficulty')
        trek.duration = request.form.get('duration')

        # When an Admin alters slot configuration, synchronize the absolute cap baseline
        new_slots = int(request.form.get('available_slots'))
        trek.total_slots = new_slots
        trek.available_slots = new_slots

        trek.assigned_staff_id = int(request.form.get('assigned_staff_id'))
        trek.trek_status = request.form.get('status')
        trek.start_date = datetime.strptime(request.form.get('start_date'), '%Y-%m-%d')
        trek.end_date = datetime.strptime(request.form.get('end_date'), '%Y-%m-%d')
        db.session.commit()
        flash('Trek Document Edited Successfully!')
        return redirect(url_for('admin_dashboard'))
    staff_list = Staff.query.filter_by(is_approved=True).all()
    return render_template('admin_edit_trek.html', trek=trek, staff_list=staff_list)


@app.route('/admin_delete_trek/<int:id>', methods=['GET', 'POST'])
def admin_remove_trek(id):
    if session.get('role') != 'admin':
        return "Unauthorized", 403
    trek = Trek.query.get_or_404(id)
    Booking.query.filter_by(trek_id=trek.id).delete()
    db.session.delete(trek)
    db.session.commit()
    flash('Trek Document Deleted Successfully!')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin_action/<string:target>/<int:id>/<string:act>')
def admin_action(target, id, act):
    if session.get('role') != 'admin':
        return "Unauthorized", 403

    if target == 'staff':
        staff = Staff.query.get_or_404(id)
        linked_user = User.query.get(staff.user_id)
        if act == 'approved' or act == 'approve':
            staff.is_approved = True
            if linked_user:
                linked_user.is_active = True
        elif act == 'blacklist':
            staff.is_approved = False
            if linked_user:
                linked_user.is_active = False
        elif act == 'unblacklist':
            staff.is_approved = True
            if linked_user:
                linked_user.is_active = True

    elif target == 'user':
        user = User.query.get_or_404(id)
        if act == 'blacklist':
            user.is_active = False
        elif act == 'unblacklist':
            user.is_active = True

    db.session.commit()
    flash('Entity configuration updated Successfully!')
    return redirect(url_for('admin_dashboard'))


@app.route('/staff_dashboard')
def staff_dashboard():
    if session.get('role') != 'staff':
        return "Unauthorized", 403

    staff_profile = Staff.query.filter_by(user_id=session.get('user_id')).first()
    if not staff_profile or not staff_profile.is_approved:
        session.clear()
        return redirect(url_for('login'))
    assigned_trek = Trek.query.filter_by(assigned_staff_id=staff_profile.id).all()
    return render_template('staff_dashboard.html', assigned_trek=assigned_trek)


@app.route('/trekker_dashboard')
def trekker_dashboard():
    if session.get('role') != 'trekker':
        return "Unauthorized", 403
    user_obj = User.query.get(session.get('user_id'))
    diff_filter = request.args.get('difficulty', '').strip()
    loc_filter = request.args.get('location', '').strip()
    query = Trek.query.filter(Trek.trek_status.in_(['Approved', 'Open']))
    if diff_filter:
        query = query.filter_by(trek_difficulty=diff_filter)
    if loc_filter:
        query = query.filter(Trek.trek_location.contains(loc_filter))

    available_treks = query.all()
    personal_booking = Booking.query.filter_by(user_id=user_obj.id).all()
    return render_template('trekker_dashboard.html', user_obj=user_obj, available_treks=available_treks,
                           personal_booking=personal_booking)


@app.route('/staff_manage_trek/<int:id>', methods=['GET', 'POST'])
def staff_manage_trek(id):
    if session.get('role') != 'staff':
        return "Unauthorized", 403

    staff_profile = Staff.query.filter_by(user_id=session.get('user_id')).first()
    trek = Trek.query.get_or_404(id)

    if trek.assigned_staff_id != staff_profile.id:
        return "Logistics clearance validation failure.", 403

    if request.method == 'POST':
        action_type = request.form.get('action_type')
        if action_type == 'update_parameters':
            # Remove any trailing commas to store raw ints and strings natively
            trek.available_slots = int(request.form.get('available_slots'))
            trek.trek_status = request.form.get('status')
            flash('Slots and Status variables pushed live.', 'success')
        elif action_type == 'mark_started':
            trek.trek_status = 'Open'
            flash('Trek operational status marked as Open.', 'info')
        elif action_type == 'mark_completed':
            trek.trek_status = 'Completed'
            bookings = Booking.query.filter_by(trek_id=trek.id, status='Booked').all()
            for b in bookings:
                b.status = 'Completed'
            flash('Trek operation cycle marked as Completed.', 'success')

        db.session.commit()
        return redirect(url_for('staff_manage_trek', id=trek.id))

    participants = Booking.query.filter_by(trek_id=trek.id).all()
    user_count = len([p for p in participants if p.status == 'Booked'])

    return render_template('staff_manage_trek.html', trek=trek, participants=participants, user_count=user_count)


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    role = session.get('role')
    user_id = session.get('user_id')
    if role == 'trekker':
        profile_obj = Trekker.query.filter_by(user_id=user_id).first_or_404()
        if request.method == 'POST':
            profile_obj.Trekker_Name = request.form.get('name')
            profile_obj.gender = request.form.get('gender')
            profile_obj.experience = request.form.get('experience')
            profile_obj.trek_history = request.form.get('trek_history')
            profile_obj.medical_condition = request.form.get('medical_condition')
            profile_obj.emergency_contact_name = request.form.get('emergency_contact_name')
            profile_obj.emergency_contact_phone = request.form.get('emergency_contact_phone')
            db.session.commit()
            flash('Profile changes done successfully.')
            return redirect(url_for('trekker_dashboard'))
        return render_template('edit_profile.html', user_obj=profile_obj)
    elif role == 'staff':
        profile_obj = Staff.query.filter_by(user_id=user_id).first_or_404()
        if request.method == 'POST':
            profile_obj.Staff_Name = request.form.get('name')
            profile_obj.contact_details = request.form.get('contact_details')
            db.session.commit()
            flash('Profile changes done successfully.')
            return redirect(url_for('staff_dashboard'))
        return render_template('edit_staff_profile.html', user_obj=profile_obj)
    return "Unauthorized", 403


@app.route('/book_trek/<int:id>')
def book_trek(id):
    if session.get('role') != 'trekker':
        return "Unauthorized", 403
    user_id = session.get('user_id')
    trek = Trek.query.get_or_404(id)

    if trek.trek_status != 'Open':
        flash('Booking rejected. Reservation are only allowed when Trek status is open.')
        return redirect(url_for('trekker_dashboard'))
    if trek.available_slots <= 0:
        flash('Overbooking not allowed! No slots remaining.')
        return redirect(url_for('trekker_dashboard'))

    trek.available_slots -= 1
    new_booking = Booking(user_id=user_id, trek_id=trek.id, status='Booked', booking_date=datetime.utcnow())
    db.session.add(new_booking)
    db.session.commit()
    flash(f'Trek booking finalized successfully for {trek.trek_name}!')
    return redirect(url_for('trekker_dashboard'))


@app.route('/bookings')
def booking_ledger():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    role = session.get('role')
    user_id = session.get('user_id')

    if role == 'admin':
        bookings = Booking.query.all()
    elif role == 'staff':
        staff_profile = Staff.query.filter_by(user_id=user_id).first_or_404()
        bookings = Booking.query.join(Trek).filter(Trek.assigned_staff_id == staff_profile.id).all()
    elif role == 'trekker':
        bookings = Booking.query.filter_by(user_id=user_id).all()
    else:
        return "Unauthorized", 403
    return render_template('bookings.html', bookings=bookings)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=8000)