from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from sqlalchemy import or_
from . import db, bcrypt
from .models import User, Product, Order, OrderItem, Review, Contact

api = Blueprint("api", __name__)

def user():
    uid = get_jwt_identity()
    return User.query.get(int(uid))

def product_json(p):
    return {"id":p.id,"name":p.name,"brand":p.brand,"category":p.category,"size":p.size,
            "price":p.price,"old_price":p.old_price,"image":p.image,"description":p.description,
            "stock":p.stock,"is_new":p.is_new}

@api.get("/health")
def health():
    return jsonify({"status":"ok","service":"SneakerHub API"})

@api.post("/auth/register")
def register():
    d=request.get_json() or {}
    if not all(d.get(k) for k in ["name","email","password"]):
        return jsonify({"message":"Thiếu thông tin bắt buộc"}),400
    if User.query.filter_by(email=d["email"].lower()).first():
        return jsonify({"message":"Email đã tồn tại"}),409
    u=User(name=d["name"],email=d["email"].lower(),password=bcrypt.generate_password_hash(d["password"]).decode())
    db.session.add(u); db.session.commit()
    return jsonify({"message":"Đăng ký thành công"}),201

@api.post("/auth/login")
def login():
    d=request.get_json() or {}
    u=User.query.filter_by(email=(d.get("email") or "").lower()).first()
    if not u or not bcrypt.check_password_hash(u.password,d.get("password","")):
        return jsonify({"message":"Email hoặc mật khẩu không đúng"}),401
    token=create_access_token(identity=str(u.id))
    return jsonify({"token":token,"user":{"id":u.id,"name":u.name,"email":u.email,"role":u.role}})

@api.get("/products")
def products():
    q=request.args.get("q","").strip()
    brand=request.args.get("brand","").strip()
    min_price=request.args.get("min_price",type=int)
    max_price=request.args.get("max_price",type=int)
    sort=request.args.get("sort","")
    query=Product.query
    if q: query=query.filter(or_(Product.name.ilike(f"%{q}%"),Product.brand.ilike(f"%{q}%")))
    if brand: query=query.filter(Product.brand.ilike(brand))
    if min_price is not None: query=query.filter(Product.price>=min_price)
    if max_price is not None: query=query.filter(Product.price<=max_price)
    if sort=="low": query=query.order_by(Product.price.asc())
    elif sort=="high": query=query.order_by(Product.price.desc())
    else: query=query.order_by(Product.created_at.desc())
    return jsonify([product_json(p) for p in query.all()])

@api.get("/products/<int:pid>")
def product_detail(pid):
    p=Product.query.get_or_404(pid)
    return jsonify(product_json(p))

@api.get("/products/<int:pid>/reviews")
def reviews(pid):
    rows=Review.query.filter_by(product_id=pid).order_by(Review.created_at.desc()).all()
    return jsonify([{"id":r.id,"rating":r.rating,"comment":r.comment,"user_id":r.user_id,"created_at":r.created_at.isoformat()} for r in rows])

@api.post("/products/<int:pid>/reviews")
@jwt_required()
def add_review(pid):
    d=request.get_json() or {}; rating=int(d.get("rating",0))
    if rating<1 or rating>5: return jsonify({"message":"Rating phải từ 1 đến 5"}),400
    if not Product.query.get(pid): return jsonify({"message":"Sản phẩm không tồn tại"}),404
    r=Review(user_id=int(get_jwt_identity()),product_id=pid,rating=rating,comment=d.get("comment",""))
    db.session.add(r); db.session.commit()
    return jsonify({"message":"Đã gửi đánh giá","id":r.id}),201

@api.post("/orders")
@jwt_required()
def create_order():
    d=request.get_json() or {}; items=d.get("items",[])
    if not items: return jsonify({"message":"Giỏ hàng trống"}),400
    customer=d.get("customer") or {}
    customer_name=d.get("customer_name") or customer.get("name") or ""
    phone=d.get("phone") or customer.get("phone") or ""
    address=d.get("address") or customer.get("address") or ""
    if not all([customer_name, phone, address]):
        return jsonify({"message":"Vui lòng nhập họ tên, số điện thoại và địa chỉ"}),400
    total=0; validated=[]
    for item in items:
        p=Product.query.get(item.get("product_id")); qty=int(item.get("quantity",0))
        if not p or qty<1: return jsonify({"message":"Sản phẩm hoặc số lượng không hợp lệ"}),400
        if p.stock<qty: return jsonify({"message":f"Không đủ tồn kho: {p.name}"}),400
        total += p.price*qty; validated.append((p,qty))
    o=Order(user_id=int(get_jwt_identity()),total=total,customer_name=customer_name,
            phone=phone,address=address,payment_method=d.get("payment_method","COD"))
    db.session.add(o); db.session.flush()
    for p,qty in validated:
        db.session.add(OrderItem(order_id=o.id,product_id=p.id,quantity=qty,price=p.price)); p.stock-=qty
    db.session.commit()
    return jsonify({"message":"Đặt hàng thành công","order_id":o.id,"total":total}),201

@api.get("/orders/my")
@jwt_required()
def my_orders():
    rows=Order.query.filter_by(user_id=int(get_jwt_identity())).order_by(Order.created_at.desc()).all()
    result=[]
    for o in rows:
        items=OrderItem.query.filter_by(order_id=o.id).all()
        result.append({"id":o.id,"total":o.total,"status":o.status,"customer_name":o.customer_name,
                       "phone":o.phone,"address":o.address,"payment_method":o.payment_method,
                       "created_at":o.created_at.isoformat(),
                       "items":[{"product_id":i.product_id,
                                  "product_name":(Product.query.get(i.product_id).name if Product.query.get(i.product_id) else "(đã xóa)"),
                                  "quantity":i.quantity,"price":i.price} for i in items]})
    return jsonify(result)

@api.post("/contact")
def contact():
    d=request.get_json() or {}
    if not all(d.get(k) for k in ["name","email","message"]): return jsonify({"message":"Thiếu thông tin"}),400
    c=Contact(name=d["name"],email=d["email"],message=d["message"]); db.session.add(c); db.session.commit()
    return jsonify({"message":"Đã nhận phản hồi"}),201

def admin_required():
    u=user()
    return u if u and u.role=="admin" else None

@api.get("/admin/products")
@jwt_required()
def admin_products():
    if not admin_required(): return jsonify({"message":"Không có quyền"}),403
    return jsonify([product_json(p) for p in Product.query.order_by(Product.id.desc()).all()])

@api.post("/admin/products")
@jwt_required()
def admin_add_product():
    if not admin_required(): return jsonify({"message":"Không có quyền"}),403
    d=request.get_json() or {}
    required=["name","brand","price"]
    if not all(d.get(k) is not None for k in required): return jsonify({"message":"Thiếu dữ liệu"}),400
    p=Product(name=d["name"],brand=d["brand"],category=d.get("category","Sneaker"),size=d.get("size","38,39,40,41,42,43"),
              price=int(d["price"]),old_price=int(d.get("old_price",0)),image=d.get("image",""),
              description=d.get("description",""),stock=int(d.get("stock",0)),is_new=bool(d.get("is_new",False)))
    db.session.add(p); db.session.commit()
    return jsonify(product_json(p)),201

@api.put("/admin/products/<int:pid>")
@jwt_required()
def admin_update_product(pid):
    if not admin_required(): return jsonify({"message":"Không có quyền"}),403
    p=Product.query.get_or_404(pid); d=request.get_json() or {}
    for k in ["name","brand","category","size","image","description"]:
        if k in d: setattr(p,k,d[k])
    for k in ["price","old_price","stock"]:
        if k in d: setattr(p,k,int(d[k]))
    if "is_new" in d: p.is_new=bool(d["is_new"])
    db.session.commit(); return jsonify(product_json(p))

@api.delete("/admin/products/<int:pid>")
@jwt_required()
def admin_delete_product(pid):
    if not admin_required(): return jsonify({"message":"Không có quyền"}),403
    p=Product.query.get_or_404(pid); db.session.delete(p); db.session.commit()
    return jsonify({"message":"Đã xóa sản phẩm"})

@api.get("/admin/orders")
@jwt_required()
def admin_orders():
    if not admin_required(): return jsonify({"message":"Không có quyền"}),403
    rows=Order.query.order_by(Order.created_at.desc()).all()
    result=[]
    for o in rows:
        items=OrderItem.query.filter_by(order_id=o.id).all()
        result.append({"id":o.id,"user_id":o.user_id,"total":o.total,"status":o.status,"customer_name":o.customer_name,
                       "phone":o.phone,"address":o.address,"payment_method":o.payment_method,
                       "created_at":o.created_at.isoformat(),
                       "items":[{"product_name":(Product.query.get(i.product_id).name if Product.query.get(i.product_id) else "(đã xóa)"),
                                  "quantity":i.quantity,"price":i.price} for i in items]})
    return jsonify(result)

@api.patch("/admin/orders/<int:oid>")
@jwt_required()
def admin_update_order(oid):
    if not admin_required(): return jsonify({"message":"Không có quyền"}),403
    o=Order.query.get_or_404(oid); status=(request.get_json() or {}).get("status")
    if status not in ["pending","confirmed","shipping","completed","cancelled"]:
        return jsonify({"message":"Trạng thái không hợp lệ"}),400
    o.status=status; db.session.commit()
    return jsonify({"message":"Đã cập nhật","status":o.status})

@api.get("/admin/contacts")
@jwt_required()
def admin_contacts():
    if not admin_required(): return jsonify({"message":"Không có quyền"}),403
    rows=Contact.query.order_by(Contact.created_at.desc()).all()
    return jsonify([{"id":c.id,"name":c.name,"email":c.email,"message":c.message,
                     "created_at":c.created_at.isoformat()} for c in rows])

@api.get("/admin/stats")
@jwt_required()
def admin_stats():
    if not admin_required(): return jsonify({"message":"Không có quyền"}),403
    orders=Order.query.all()
    revenue=sum(o.total for o in orders if o.status!="cancelled")
    return jsonify({
        "total_products": Product.query.count(),
        "total_orders": len(orders),
        "total_customers": User.query.filter_by(role="customer").count(),
        "total_revenue": revenue,
        "pending_orders": sum(1 for o in orders if o.status=="pending"),
        "low_stock": Product.query.filter(Product.stock<=5).count(),
    })
