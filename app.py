from flask import Flask, render_template, request, redirect, url_for, session, flash
from datetime import timedelta
import mysql.connector as sql
from banking_logic import Operations, User, connect_db
import email_system as ems
import os
import re

# app = Flask(__name__)
# # If you want auto-logout on restart keep random, else use env var
# app.secret_key = os.urandom(24)
# app.permanent_session_lifetime = timedelta(hours=4)

app = Flask(__name__)
# app.secret_key = "super_secret_key_123"  
app.secret_key = os.urandom(24)
app.permanent_session_lifetime = timedelta(minutes=5)

opt = Operations()

# def init_db():
#     try:
#         conn = sql.connect(
#             host='localhost',
#             user='root',
#             password='root',
#         )
#         cursor = conn.cursor()
#         cursor.execute("SHOW DATABASES")
#         if ("flask_banking_system",) not in cursor.fetchall():
#             cursor.execute("CREATE DATABASE IF NOT EXISTS flask_banking_system")
#         cursor.execute("USE flask_banking_system")
#         cursor.execute("""CREATE TABLE IF NOT EXISTS users (
#             account_number VARCHAR(20) NOT NULL PRIMARY KEY,
#             user_name VARCHAR(100),
#             pin VARCHAR(20),
#             balance DECIMAL(10,2) DEFAULT 1000.00,
#             email VARCHAR(100),
#             is_admin TINYINT(1) DEFAULT 0
#         );""")
#         cursor.execute("""CREATE TABLE IF NOT EXISTS transactions (
#             id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
#             account_number VARCHAR(20),
#             transaction_details VARCHAR(100),
#             debit DECIMAL(10,2),
#             credit DECIMAL(10,2),
#             balance DECIMAL(10,2),
#             transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#         );""")
#         # If table existed earlier without is_admin, try to add
#         try:
#             cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin TINYINT(1) DEFAULT 0;")
#         except Exception:
#             pass
#         conn.commit()
#         conn.close()
#     except sql.Error as e:
#         print("DB init error:", e)

# init_db()

# --------- Helpers ----------
def current_user():
    data = session.get("user")
    if not data:
        return None
    user = opt.login(data["account_number"], data["pin"])
    if user:
        session["user"] = {
            "account_number": user.account_number,
            "user_name": user.user_name,
            "pin": user.pin,
            "email_name": user.email_name,
            "balance": float(user.balance),
            "is_admin": int(user.is_admin)
        }
    return user

def login_required(view):
    from functools import wraps
    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("user"):
            flash("Please log in first.", "warning")
            return redirect(url_for("login_page"))
        return view(*args, **kwargs)
    return wrapper

def admin_required(view):
    from functools import wraps
    @wraps(view)
    def wrapper(*args, **kwargs):
        u = session.get("user")
        if not u or not u.get("is_admin"):
            flash("Access denied. Admins only.", "danger")
            return redirect(url_for("main_menu") if u else url_for("login_page"))
        return view(*args, **kwargs)
    return wrapper


@app.route("/testdb")
def test_db():
    conn = connect_db()
    if conn:
        return "✅ DB connected successfully"
    else:
        return "❌ DB connection failed"


# --------- Auth ----------
@app.route("/")
def home():
    if session.get("user"):
        return redirect(url_for("main_menu"))
    return redirect(url_for("login_page"))

@app.route("/login", methods=["GET"])
def login_page():
    # session.pop("reset", None) #because forgot.html
    session.clear()
    return render_template("login.html", title="Login")

@app.route("/login", methods=["POST"])
def login_post():
    acc = request.form.get("account", "").strip()
    pin = request.form.get("pin", "").strip()
    if not acc or not pin:
        flash("Enter both account and PIN.", "warning")
        return redirect(url_for("login_page"))
    user = opt.login(acc, pin)
    if user:
        session["user"] = {
            "account_number": user.account_number,
            "user_name": user.user_name,
            "pin": user.pin,
            "email_name": user.email_name,
            "balance": float(user.balance),
            "is_admin": int(user.is_admin)
        }
        session["user_id"] = user.account_number 
        flash(f"Welcome {user.user_name}!", "success")
        # Admins can be redirected to admin dashboard if you prefer:
        # return redirect(url_for("admin_dashboard") if user.is_admin else url_for("main_menu"))
        return redirect(url_for("main_menu"))
    flash("Invalid credentials.", "danger")
    return redirect(url_for("login_page"))

@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for("login_page"))

# --------- Signup ----------
@app.route("/signup", methods=["GET"])
def signup_page():
    session.pop("reset", None) 
    return render_template("signup.html", title="Sign Up")

@app.route("/signup", methods=["POST"])
def signup_post():
    action = request.form.get("action")

    # ----------- STEP 1: Send OTP -----------
    if action == "send_otp":
        email = request.form.get("email", "").strip()
        name  = request.form.get("name", "").strip().title()

        if not re.match(r"^[A-Za-z\s]{3,30}$", name):
            flash("Invalid name. Only letters and spaces (3–30 chars) allowed.", "danger")
            return redirect(url_for("signup_page"))

        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}$", email):
            flash("Enter a valid email address.", "danger")
            return redirect(url_for("signup_page"))

        subject = "OTP for Create New Account into Bankify App"
        email_text = "is your OTP for Sign up into Bankify App."
        otp = ems.otp_genrater(email, subject, email_text)

        if otp:
            session["signup"] = {"email": email, "name": name, "otp": str(otp)}
            flash("OTP sent to your email.", "info")
        else:
            flash("Failed to send OTP. Check email settings.", "danger")

        return redirect(url_for("signup_page"))

    # ----------- STEP 2: Verify OTP + Create Account -----------
    elif action == "create_account":
        otp_in = request.form.get("otp", "").strip()
        pin    = request.form.get("pin", "").strip()

        data = session.get("signup")
        if not data:
            flash("Please request OTP first.", "warning")
            return redirect(url_for("signup_page"))

        if not re.match(r"^[0-9]{6}$", otp_in):
            flash("OTP must be a 6-digit number.", "danger")
            return redirect(url_for("signup_page"))

        if str(otp_in) != str(data.get("otp")):
            flash("OTP verification failed.", "danger")
            return redirect(url_for("signup_page"))

        if not re.match(r"^[0-9]{4,6}$", pin):
            flash("PIN must be 4 to 6 digits.", "danger")
            return redirect(url_for("signup_page"))

        # Save PIN in data
        data["pin"] = pin

        # Create Account
        account_number = opt.generate_unique_account_number()
        user = opt.add_user(data["email"], account_number, data["name"], data["pin"])

        if user:
            session.pop("signup", None)
            session["user"] = {
                "account_number": user.account_number,
                "user_name": user.user_name,
                "pin": user.pin,
                "email_name": user.email_name,
                "balance": float(user.balance),
                "is_admin": int(user.is_admin)
            }
            flash(f"Account created. Your account number is {account_number}", "success")
            return redirect(url_for("main_menu"))

        flash("Something went wrong during signup.", "danger")
        return redirect(url_for("signup_page"))

    # ----------- Unknown Action -----------
    else:
        flash("Invalid action.", "danger")
        return redirect(url_for("signup_page"))


# --------- User features ----------
@app.route("/menu")
@login_required
def main_menu():
    user = current_user()
    return render_template("main_menu.html", user=user, title="Main Menu")

@app.route("/balance")
@login_required
def balance():
    user = current_user()
    bal = opt.show_balance(user)
    flash(f"Current Balance: ₹{bal}", "info")
    return redirect(url_for("main_menu"))

@app.route("/account")
@login_required
def account_details():
    user = current_user()
    details = opt.account_details(user)
    return render_template("account_details.html", details=details, title="Account Details")

@app.route("/withdraw", methods=["GET","POST"])
@login_required
def withdraw():
    user = current_user()
    if request.method == "POST":
        try:
            amount = float(request.form.get("amount","0"))
        except ValueError:
            flash("Enter a valid number.", "danger")
            return redirect(url_for("withdraw"))
        msg = opt.withdraw(user, amount)
        if "Withdraw" in msg:
            flash(msg, "success")
        else:
            flash(msg, "warning")
        return redirect(url_for("main_menu"))
    return render_template("withdraw.html", title="Withdraw")

@app.route("/deposit", methods=["GET","POST"])
@login_required
def deposit():
    user = current_user()
    if request.method == "POST":
        try:
            amount = float(request.form.get("amount","0"))
        except ValueError:
            flash("Enter a valid number.", "danger")
            return redirect(url_for("deposit"))
        msg = opt.deposit(user, amount)
        flash(msg, "success")
        return redirect(url_for("main_menu"))
    return render_template("deposit.html", title="Deposit")

@app.route("/transfer", methods=["GET","POST"])
@login_required
def transfer():
    user = current_user()
    if request.method == "POST":
        recipient = request.form.get("recipient_account", "").strip()
        try:
            amount = float(request.form.get("amount", "0"))
        except ValueError:
            flash("Enter a valid number.", "danger")
            return redirect(url_for("transfer"))

        if not recipient:
            flash("Enter a recipient account number.", "warning")
            return redirect(url_for("transfer"))

        if user.account_number == recipient:
            flash("Cannot transfer to your own account.", "warning")
            return redirect(url_for("transfer"))

        if not opt.check_account(user, recipient):
            flash("Recipient account number is not valid.", "danger")
            return redirect(url_for("transfer"))

        res = opt.transfer(user, recipient, amount)
        category = "success" if "Transferred to" in res else ("warning" if "Insufficient" in res else "danger")
        flash(res, category)
        return redirect(url_for("main_menu"))

    return render_template("transfer.html", title="Transfer")

@app.route("/transaction_history")
@login_required
def transactions():
    user = current_user()
    details = opt.show_transaction_history(user)
    return render_template("transaction_history.html", rows=details, title="Transactions")

@app.route("/send-statement")
@login_required
def send_statement():
    user = current_user()
    ok = opt.send_statement(user)
    if ok:
        flash("Statement has been sent to your email.", "success")
    else:
        flash("Something went wrong while sending statement.", "danger")
    return redirect(url_for("main_menu"))

# --------- Admin: Dashboard & Users ----------
@app.route("/admin")
@admin_required
def admin_dashboard():
    return render_template("admin_dashboard.html", title="Admin Dashboard")

@app.route("/admin/users")
@admin_required
def admin_users():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT account_number, user_name, email, balance, is_admin FROM users ORDER BY account_number ASC")
    users = cursor.fetchall()
    conn.close()
    return render_template("admin_users.html", users=users, title="Manage Users")

@app.route("/admin/users/create", methods=["GET","POST"])
@admin_required
def admin_create_user():
    if request.method == "POST":
        name = request.form.get("user_name","").strip().title()
        email = request.form.get("email","").strip()
        pin = request.form.get("pin","").strip()
        opening_balance = float(request.form.get("balance","1000") or 1000)
        make_admin = int(request.form.get("is_admin","0"))

        if not re.match(r"^[A-Za-z\s]{3,30}$", name):
            flash("Invalid name (3–30 letters/spaces).", "danger")
            return redirect(url_for("admin_create_user"))
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}$", email):
            flash("Invalid email.", "danger")
            return redirect(url_for("admin_create_user"))
        if not re.match(r"^[0-9]{4,6}$", pin):
            flash("PIN must be 4–6 digits.", "danger")
            return redirect(url_for("admin_create_user"))

        acc = opt.generate_unique_account_number()
        opt.admin_create_user(email, acc, name, pin, opening_balance, make_admin)
        flash(f"User created. Account No: {acc}", "success")
        return redirect(url_for("admin_users"))
    return render_template("admin_create_user.html", title="Create User")

@app.route("/admin/users/<account_number>/edit", methods=["GET","POST"])
@admin_required
def admin_edit_user(account_number):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT account_number, user_name, email, pin, is_admin FROM users WHERE account_number=%s", (account_number,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        flash("User not found.", "danger")
        return redirect(url_for("admin_users"))

    if request.method == "POST":
        name = request.form.get("user_name","").strip().title()
        pin = request.form.get("pin","").strip()
        make_admin = int(request.form.get("is_admin","0"))
        if name and not re.match(r"^[A-Za-z\s]{3,30}$", name):
            flash("Invalid name.", "danger")
            conn.close()
            return redirect(url_for("admin_edit_user", account_number=account_number))
        if pin and not re.match(r"^[0-9]{4,6}$", pin):
            flash("PIN must be 4–6 digits.", "danger")
            conn.close()
            return redirect(url_for("admin_edit_user", account_number=account_number))
        cursor.execute("UPDATE users SET user_name=%s, pin=%s, is_admin=%s WHERE account_number=%s",
                       (name or user["user_name"], pin or user["pin"], make_admin, account_number))
        conn.commit()
        conn.close()
        flash("User updated.", "success")
        return redirect(url_for("admin_users"))

    conn.close()
    return render_template("admin_edit_user.html", u=user, title="Edit User")

@app.route("/admin/users/<account_number>/delete", methods=["POST"])
@admin_required
def admin_delete_user(account_number):
    opt.admin_delete_user(account_number)
    flash("User deleted.", "warning")
    return redirect(url_for("admin_users"))

@app.route("/admin/users/<account_number>/balance", methods=["GET","POST"])
@admin_required
def admin_adjust_balance(account_number):
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT account_number, user_name, balance FROM users WHERE account_number=%s", (account_number,))
    user = cursor.fetchone()
    if not user:
        conn.close()
        flash("User not found.", "danger")
        return redirect(url_for("admin_users"))

    if request.method == "POST":
        try:
            amount = float(request.form.get("amount","0"))
        except ValueError:
            flash("Enter a valid amount.", "danger")
            conn.close()
            return redirect(url_for("admin_adjust_balance", account_number=account_number))
        action = request.form.get("action")  # add/subtract
        if action == "subtract":
            amount = -abs(amount)
        else:
            amount = abs(amount)
        ok = opt.admin_adjust_balance(account_number, amount)
        conn.close()
        if ok:
            flash("Balance adjusted.", "success")
        else:
            flash("Failed to adjust balance.", "danger")
        return redirect(url_for("admin_users"))

    conn.close()
    return render_template("admin_adjust_balance.html", u=user, title="Adjust Balance")

# --------- Admin: Transactions & Summary ----------
@app.route("/admin/transactions")
@admin_required
def admin_transactions():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id, account_number, transaction_details, debit, credit, balance, transaction_date 
        FROM transactions ORDER BY id DESC LIMIT 200
    """)
    txns = cursor.fetchall()
    conn.close()
    return render_template("admin_transactions.html", txns=txns, title="All Transactions")

@app.route("/admin/summary")
@admin_required
def admin_summary():
    conn = connect_db()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT COUNT(*) AS total_users, SUM(balance) AS total_balance FROM users")
    row = cursor.fetchone()
    total_users = row["total_users"] or 0
    total_balance = row["total_balance"] or 0.00

    cursor.execute("SELECT SUM(credit) AS total_credits, SUM(debit) AS total_debits FROM transactions")
    row2 = cursor.fetchone()
    total_credits = row2["total_credits"] or 0.00
    total_debits = row2["total_debits"] or 0.00
    conn.close()
    return render_template("admin_summary.html",
                           total_users=total_users,
                           total_balance=total_balance,
                           total_credits=total_credits,
                           total_debits=total_debits,
                           title="Bank Summary")

# ---------------- Change PIN ----------------
@app.route("/change_pin", methods=["GET", "POST"])
@login_required
def change_pin():
    session.pop("reset", None) #because forgot.html
    if request.method == "POST":
        current_pin = request.form.get("current_pin")
        new_pin = request.form.get("new_pin")
        confirm_pin = request.form.get("confirm_pin")

        user = current_user()
        conn = connect_db()
        cursor = conn.cursor()

        # Check old PIN
        # print("DEBUG user:", user, type(user))
        cursor.execute("SELECT pin FROM users WHERE account_number=%s", (user.account_number,))
        db_pin = cursor.fetchone()[0]

        if db_pin != current_pin:
            flash("Current PIN is incorrect.", "danger")
            return redirect(url_for("change_pin"))

        if new_pin != confirm_pin:
            flash("New PIN and Confirm PIN do not match.", "danger")
            return redirect(url_for("change_pin"))

        # Update PIN
        cursor.execute("UPDATE users SET pin=%s WHERE account_number=%s", (new_pin, user.account_number))
        conn.commit()
        cursor.close()
        conn.close()

        flash(" PIN changed successfully!", "success")
        return redirect(url_for("main_menu"))

    return render_template("change_pin.html", title="Change PIN")


# ---------------- Forgot PIN ----------------
@app.route("/forgot", methods=["GET"])
def forgot_page():
    return render_template("forgot.html", title="Forgot PIN")

@app.route("/forgot", methods=["POST"])
def forgot_post():
    acc = request.form.get("account","").strip()
    email = request.form.get("email","").strip()
    action = request.form.get("action")

    # STEP 1 → Send OTP
    if action == "send_otp":
        if not re.match(r"^[A-Za-z\s]{3,30}$", name):
            flash("Invalid name. Only letters and spaces (3–30 chars) allowed.", "danger")
            return redirect(url_for("signup_page"))
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}$", email):
            flash("Enter a valid email address.", "danger")
            return redirect(url_for("signup_page"))
    
        subject = "OTP for Create New Account into Bankify App"
        email_text = "is your OTP for Sign up into Bankify App."
        otp = ems.otp_genrater(email, subject, email_text)
    
        if otp:
            session["signup"] = {"email": email, "name": name, "otp": str(otp)}
            flash("OTP sent to your email.", "info")
        else:
            flash("Failed to send OTP. Check email settings.", "danger")
        return redirect(url_for("signup_page"))
    
    # STEP 2 → Create Account
    if action == "create_account":
        data = session.get("signup", {})
        if not data:
            flash("Please request OTP first.", "warning")
            return redirect(url_for("signup_page"))
    
        if not re.match(r"^[0-9]{6}$", otp_in):
            flash("OTP must be a 6-digit number.", "danger")
            return redirect(url_for("signup_page"))
    
        if str(otp_in) != str(data.get("otp")):
            flash("OTP verification failed.", "danger")
            return redirect(url_for("signup_page"))
    
        if not re.match(r"^[0-9]{4,6}$", pin):
            flash("PIN must be 4 to 6 digits.", "danger")
            return redirect(url_for("signup_page"))
    
        # save pin
        data["pin"] = pin
    
        # create account
        account_number = opt.generate_unique_account_number()
        user = opt.add_user(data["email"], account_number, data["name"], data["pin"])
        if user:
            session.pop("signup", None)
            session["user"] = {
                "account_number": user.account_number,
                "user_name": user.user_name,
                "pin": user.pin,
                "email_name": user.email_name,
                "balance": float(user.balance),
                "is_admin": int(user.is_admin)
            }
            flash(f"Account created. Your account number is {account_number}", "success")
            return redirect(url_for("main_menu"))
    
        flash("Something went wrong during signup.", "danger")
        return redirect(url_for("signup_page"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)





