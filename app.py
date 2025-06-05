from Flask import Flask, render_template, request, redirect, url_for, session
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key_here' # Replace with a strong secret key

# Database initialization
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand TEXT NOT NULL,
            price REAL NOT            NULL,
            description TEXT,
            image_url TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Call once to initialize the database
init_db()

# --- Routes ---

@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products LIMIT 6") # Display some featured products
    featured_products = cursor.fetchall()
    conn.close()
    return render_template('index.html', products=featured_products)

@app.route('/products')
def products():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products")
    all_products = cursor.fetchall()
    conn.close()
    return render_template('products.html', products=all_products)

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    if product:
        return render_template('product_detail.html', product=product)
    return "Product not found", 404

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    if 'cart' not in session:
        session['cart'] = []
    
    # In a real app, you'd fetch product details to store more info in cart
    # For simplicity, we'll just store product_id
    session['cart'].append(product_id)
    session.modified = True # Important for list/dict modifications
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    cart_items = []
    total_price = 0
    if 'cart' in session and session['cart']:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        for product_id in session['cart']:
            cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
            product = cursor.fetchone()
            if product:
                cart_items.append(product)
                total_price += product[3] # Assuming price is at index 3
        conn.close()
    return render_template('cart.html', cart_items=cart_items, total_price=total_price)

@app.route('/remove_from_cart/<int:product_id>')
def remove_from_cart(product_id):
    if 'cart' in session and product_id in session['cart']:
        session['cart'].remove(product_id)
        session.modified = True
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        # Process order (e.g., save to orders table, clear cart)
        # For simplicity, just clear the cart and redirect
        session.pop('cart', None)
        return render_template('checkout_success.html')
    return render_template('checkout.html')

# --- User Authentication (Basic) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cursor.fetchone()
        conn.close()
        if user:
            session['logged_in'] = True
            session['username'] = user[1]
            return redirect(url_for('index'))
        else:
            return "Invalid Credentials"
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            return "Username already exists"
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('cart', None) # Clear cart on logout
    return redirect(url_for('index'))


# --- Admin Route (Example for adding products) ---
@app.route('/admin/add_product', methods=['GET', 'POST'])
def admin_add_product():
    # In a real app, you'd add authentication/authorization for admin users
    if request.method == 'POST':
        name = request.form['name']
        brand = request.form['brand']
        price = float(request.form['price'])
        description = request.form['description']
        image_url = request.form['image_url']
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO products (name, brand, price, description, image_url) VALUES (?, ?, ?, ?, ?)",
                       (name, brand, price, description, image_url))
        conn.commit()
        conn.close()
        return "Product added successfully!"
    return render_template('admin_add_product.html') # A simple form to add product

if __name__ == '__main__':
    app.run(debug=True) # debug=True for development, set to False in production