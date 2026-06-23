from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime
import re

app = Flask(__name__)
app.secret_key = "nhaboi123"

# ==========================
# KHỞI TẠO DATABASE
# ==========================
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    # 1. BẢNG USERS
    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT
    )
    """)
    # Tạo tài khoản admin mặc định
    try:
        c.execute("INSERT INTO users(username,password) VALUES (?,?)", ("admin", "123456"))
    except:
        pass

    # 2. BẢNG ORDERS
    c.execute("""
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        product_name TEXT,
        price INTEGER
    )
    """)
    columns = [
        ("full_name", "TEXT"), ("phone", "TEXT"), ("address", "TEXT"),
        ("status", "TEXT DEFAULT 'Chờ xử lý'"), ("created_at", "TEXT"), ("completed_at", "TEXT")
    ]
    for col_name, col_type in columns:
        try:
            c.execute(f"ALTER TABLE orders ADD COLUMN {col_name} {col_type}")
        except:
            pass

    # 3. BẢNG PRODUCTS (Thực đơn)
    # Xóa bảng cũ đi để cập nhật hình ảnh mới nhất
    c.execute("DROP TABLE IF EXISTS products")
    
    # Tạo lại bảng với cột image
    c.execute("""
    CREATE TABLE products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        price INTEGER,
        category TEXT,
        image TEXT
    )
    """)

    # Nạp 32 món ăn kèm TÊN ẢNH CHÍNH XÁC
    products = [
        ("Trà tắc", 10000, "Trà", "1.jpg"), 
        ("Trà chanh", 10000, "Trà", "image_15f921.jpg"), 
        ("Trà tắc thái xanh", 10000, "Trà", "image_15f964.jpg"),
        ("Trà chanh thái xanh", 15000, "Trà", "image_15f964.jpg"), 
        ("Trà tắc xí muội", 15000, "Trà", "image_15f8cA7.jpg"), 
        ("Trà me hạt dẻo", 20000, "Trà", "image_15f8c7.jpg"),

        ("Trà chanh dây", 15000, "Trà trái cây", "image_15f9a0.jpg"), 
        ("Trà việt quất", 15000, "Trà trái cây", "image_15f95e.jpg"),
        ("Trà ổi hồng", 18000, "Trà trái cây", "image_15f8e8.jpg"), 
        ("Trà dâu tằm", 15000, "Trà trái cây", "image_15f95e.jpg"),
        ("Trà vải", 20000, "Trà trái cây", "image_15f8e8.jpg"), 
        ("Trà đào", 15000, "Trà trái cây", "image_15f9a0.jpg"),

        ("Trà sữa truyền thống", 15000, "Trà sữa", "image_15f921.jpg"), 
        ("Trà sữa thái xanh", 15000, "Trà sữa", "image_15f964.jpg"),
        ("Trà sữa khoai môn", 18000, "Trà sữa", "image_15f907.jpg"), 
        ("Trà sữa gạo rang", 18000, "Trà sữa", "image_15fd26.jpg"),
        ("Trà sữa socola", 25000, "Trà sữa", "image_15f907.jpg"), 
        ("Trà sữa caramel", 25000, "Trà sữa", "image_15fd26.jpg"), 
        ("Trà sữa phô mai", 30000, "Trà sữa", "image_15f907.jpg"),

        ("Matcha Latte", 18000, "Latte", "matcha.jpeg"), 
        ("Khoai môn Latte", 18000, "Latte", "image_15f984.jpg"), 
        ("Cacao Latte", 18000, "Latte", "image_15f984.jpg"),
        ("Matcha đào", 19000, "Latte", "image_15f8e2.jpg"), 
        ("Coco Matcha", 28000, "Latte", "image_15f984.jpg"),

        ("Sữa chua nguyên vị", 23000, "Sữa chua", "image_15f964.jpg"), 
        ("Sữa chua việt quất", 25000, "Sữa chua", "image_15f95e.jpg"), 
        ("Sữa chua đào", 25000, "Sữa chua", "image_15f9a0.jpg"),

        ("Đá bào sữa", 10000, "Đá bào", "image_15fd26.jpg"), 
        ("Milo dầm", 20000, "Đá bào", "image_15fd26.jpg"),

        ("Bánh tráng trộn", 15000, "Ăn vặt", "image_16e203.jpg"), 
        ("Khô gà", 90000, "Ăn vặt", "image_16e203.jpg"), 
        ("Tóp mỡ", 39000, "Ăn vặt", "image_16e203.jpg")
    ]
    c.executemany("INSERT INTO products(name,price,category,image) VALUES (?,?,?,?)", products)

    conn.commit()
    conn.close()

# Gọi hàm khởi tạo DB khi bắt đầu chạy
init_db()


# ==========================
# CÁC ROUTE GIAO DIỆN
# ==========================

@app.route("/")
def home():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    conn.close()
    return render_template("index.html", products=products)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        # Validation
        if not username or not password:
            return render_template("register.html", error="❌ Vui lòng điền đầy đủ thông tin")
        
        if len(username) < 3:
            return render_template("register.html", error="❌ Tên đăng nhập phải ít nhất 3 ký tự")
        
        if len(password) < 4:
            return render_template("register.html", error="❌ Mật khẩu phải ít nhất 4 ký tự")
        
        if not re.match("^[a-zA-Z0-9_.-]+$", username):
            return render_template("register.html", error="❌ Tên đăng nhập chỉ chứa chữ, số, _, ., -")
        
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users(username,password) VALUES (?,?)", (username, password))
            conn.commit()
            conn.close()
            return redirect("/login")
        except sqlite3.IntegrityError:
            conn.close()
            return render_template("register.html", error="❌ Tên đăng nhập đã tồn tại")
        except Exception as e:
            conn.close()
            return render_template("register.html", error="❌ Lỗi hệ thống, vui lòng thử lại")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()
        
        if not username or not password:
            return render_template("login.html", error="❌ Vui lòng nhập tài khoản và mật khẩu")
        
        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session["user"] = username
            return redirect("/")
        return render_template("login.html", error="❌ Sai tài khoản hoặc mật khẩu")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/add/<int:id>")
def add(id):
    if "user" not in session: 
        return redirect("/login")
    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE id=?", (id,))
    product = c.fetchone()
    conn.close()
    
    if not product:
        return redirect("/")
    
    # Get size and price from URL (for reference), but recalculate price based on base price + size markup
    size = request.args.get("size", "500ml")
    
    # Base price from database
    base_price = product[2]
    
    # Calculate final price based on size (same logic as frontend)
    category = product[3]
    final_price = base_price
    
    if category in ["Trà sữa", "Latte"]:
        if size == "700ml":
            final_price = base_price + 7000
        elif size == "1 Lít":
            final_price = base_price + 12000
    elif category in ["Trà", "Trà trái cây"]:
        if size == "700ml":
            final_price = base_price + 5000
        elif size == "1 Lít":
            final_price = base_price + 10000
        elif size == "1.2 Lít":
            final_price = base_price + 15000
    elif category == "Ăn vặt":
        if size == "Phần Lớn":
            final_price = base_price + 20000
    else:
        if size == "Size L":
            final_price = base_price + 5000
    
    if "cart" not in session: 
        session["cart"] = []
    
    cart = session["cart"]
    cart.append({"name": product[1], "price": final_price, "size": size})
    session["cart"] = cart
    return redirect("/")


@app.route("/remove/<int:index>")
def remove(index):
    if "user" not in session: 
        return redirect("/login")
    
    if "cart" in session:
        cart = session["cart"]
        if 0 <= index < len(cart):
            cart.pop(index) 
            session["cart"] = cart
            
    return redirect("/cart")


@app.route("/cart")
def cart():
    cart = session.get("cart", [])
    total = sum(item["price"] for item in cart)
    return render_template("cart.html", cart=cart, total=total)


@app.route("/checkout", methods=["POST"])
def checkout():
    if "user" not in session: 
        return redirect("/login")
    
    full_name = request.form.get("full_name", "").strip()
    phone = request.form.get("phone", "").strip()
    address = request.form.get("address", "").strip()
    cart = session.get("cart", [])
    
    # Validation
    if not full_name or not phone or not address:
        return "<h1>❌ Lỗi: Vui lòng điền đầy đủ thông tin</h1><a href='/cart'>Quay lại giỏ hàng</a>"
    
    # Validate phone (10-11 digits)
    if not re.match(r"^[0-9]{10,11}$", phone.replace(" ", "").replace("-", "")):
        return "<h1>❌ Lỗi: Số điện thoại không hợp lệ (phải 10-11 chữ số)</h1><a href='/cart'>Quay lại giỏ hàng</a>"
    
    # Validate address (at least 10 characters)
    if len(address) < 10:
        return "<h1>❌ Lỗi: Địa chỉ quá ngắn, vui lòng chi tiết hơn</h1><a href='/cart'>Quay lại giỏ hàng</a>"
    
    if not cart:
        return "<h1>❌ Lỗi: Giỏ hàng trống!</h1><a href='/'>Về trang chủ</a>"
    
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    total = sum(item["price"] for item in cart)

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    try:
        order_id = None
        for item in cart:
            c.execute("""
            INSERT INTO orders(username, full_name, phone, address, product_name, price, status, created_at)
            VALUES (?,?,?,?,?,?,?,?)
            """, (session["user"], full_name, phone, address, item["name"], item["price"], "Chờ xử lý", now))
            if order_id is None:
                order_id = c.lastrowid
        
        conn.commit()
        session["cart"] = []
        
        return render_template("success.html", 
                             order_id=order_id,
                             full_name=full_name,
                             phone=phone,
                             address=address,
                             total=total,
                             created_at=now)
    except Exception as e:
        conn.rollback()
        return f"<h1>❌ Lỗi: Không thể lưu đơn hàng</h1><a href='/cart'>Thử lại</a>"
    finally:
        conn.close()


# ==========================
# USER ORDERS MANAGEMENT
# ==========================
@app.route("/my-orders")
def my_orders():
    if "user" not in session: 
        return redirect("/login")
    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
    SELECT id, username, full_name, phone, address, product_name, price, status, created_at, completed_at
    FROM orders WHERE username = ? ORDER BY id DESC
    """, (session["user"],))
    orders = c.fetchall()
    conn.close()
    
    return render_template("user_orders.html", orders=orders, session=session)


@app.route("/order-detail/<int:order_id>")
def order_detail(order_id):
    if "user" not in session: 
        return redirect("/login")
    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
    SELECT id, username, full_name, phone, address, product_name, price, status, created_at, completed_at
    FROM orders WHERE id = ? AND username = ?
    """, (order_id, session["user"]))
    order = c.fetchone()
    conn.close()
    
    if not order:
        return "<h1>❌ Không tìm thấy đơn hàng</h1><a href='/my-orders'>Quay lại</a>"
    
    return render_template("order_detail.html", order=order, session=session)


@app.route("/cancel-order/<int:order_id>")
def cancel_order(order_id):
    if "user" not in session: 
        return redirect("/login")
    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    
    # Kiểm tra đơn hàng thuộc user
    c.execute("SELECT status FROM orders WHERE id = ? AND username = ?", (order_id, session["user"]))
    result = c.fetchone()
    
    if not result:
        conn.close()
        return "<h1>❌ Không tìm thấy đơn hàng</h1><a href='/my-orders'>Quay lại</a>"
    
    # Nếu đơn hàng đã hoàn thành, không cho phép hủy
    if result[0] == "Hoàn thành":
        conn.close()
        return "<h1>❌ Không thể hủy đơn hàng đã hoàn thành</h1><a href='/my-orders'>Quay lại</a>"
    
    # Hủy đơn hàng
    try:
        c.execute("UPDATE orders SET status = 'Đã hủy' WHERE id = ?", (order_id,))
        conn.commit()
        conn.close()
        return redirect("/my-orders")
    except:
        conn.close()
        return "<h1>❌ Lỗi hệ thống, vui lòng thử lại</h1><a href='/my-orders'>Quay lại</a>"
@app.route("/admin")
def admin():
    if "user" not in session: return redirect("/login")
    if session["user"] != "admin": return "Bạn không có quyền truy cập"

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("""
    SELECT id, username, full_name, phone, address, product_name, price, status, created_at, completed_at
    FROM orders ORDER BY id DESC
    """)
    orders = c.fetchall()
    conn.close()
    return render_template("admin.html", orders=orders)


@app.route("/admin/complete/<int:order_id>")
def complete_order(order_id):
    if session.get("user") != "admin": return redirect("/login")
    
    now = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE orders SET status = 'Hoàn thành', completed_at = ? WHERE id = ?", (now, order_id))
    conn.commit()
    conn.close()
    return redirect("/admin")


@app.route("/admin/delete/<int:order_id>")
def delete_order(order_id):
    if session.get("user") != "admin": return redirect("/login")
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    conn.commit()
    conn.close()
    return redirect("/admin")


if __name__ == "__main__":
    app.run(debug=True)