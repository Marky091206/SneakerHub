from . import db, bcrypt
from .models import User, Product

def seed_database():
    if User.query.first():
        return

    admin = User(
        name="SneakerHub Admin",
        email="admin@sneakerhub.vn",
        password=bcrypt.generate_password_hash("admin123").decode(),
        role="admin"
    )
    customer = User(
        name="Demo Customer",
        email="customer@sneakerhub.vn",
        password=bcrypt.generate_password_hash("123456").decode(),
        role="customer"
    )
    db.session.add_all([admin, customer])

    products = [
        Product(name="Air Max 270", brand="Nike", price=3290000, old_price=3890000, stock=20, is_new=False, image="https://images.unsplash.com/photo-1542291026-7eec264c27ff"),
        Product(name="Ultraboost Light", brand="Adidas", price=3590000, old_price=4290000, stock=15, is_new=False, image="https://images.unsplash.com/photo-1608231387042-66d1773070a5"),
        Product(name="RS-X Heritage", brand="Puma", price=2490000, stock=18, is_new=True, image="https://images.unsplash.com/photo-1543508282-6319a3e2621f"),
        Product(name="Chuck 70 Classic", brand="Converse", price=1890000, old_price=2190000, stock=25, is_new=False, image="https://images.unsplash.com/photo-1495555961986-6d4c1ecb7be3"),
        Product(name="530 White Silver", brand="New Balance", price=2890000, stock=12, is_new=True, image="https://images.unsplash.com/photo-1539185441755-769473a23570"),
    ]
    db.session.add_all(products)
    db.session.commit()
