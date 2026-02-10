from app import app
from models import db, Admin
from werkzeug.security import generate_password_hash

with app.app_context():
    username = "laforet26"          # 🔴 BURAYI DEĞİŞTİR
    password = "SSrs550!"  # 🔴 BURAYI DEĞİŞTİR

    # eski admin varsa sil
    old = Admin.query.filter_by(username=username).first()
    if old:
        db.session.delete(old)
        db.session.commit()

    admin = Admin(
        username=username,
        password=generate_password_hash(password)
    )

    db.session.add(admin)
    db.session.commit()

    print("✅ Admin başarıyla oluşturuldu")
