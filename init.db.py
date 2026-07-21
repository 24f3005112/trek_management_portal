from app import app, db, User

with app.app_context():

    db.create_all()

    admin = User.query.filter_by(role="admin").first()
    if admin is None:
        new_admin = User(
            email="admin@iitm.ac.in",
            password="admin@123",
            role="admin"
        )
        db.session.add(new_admin)
        db.session.commit()

        print("Admin created")
    else:
        print("Admin already exists")