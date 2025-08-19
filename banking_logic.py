import email_system as ems
import os
from decimal import Decimal
import mysql.connector as sql
# from flask_login import UserMixin

# def connect_db():
#     try:
#         conn = sql.connect(
#             host='localhost',
#             user='root',
#             password='root',
#             database='flask_banking_system'
#         )
#     except sql.Error as e:
#         print("Error while connecting to database:", e)
#         return None
#     else:
#         return conn
    
import mysql.connector as sql
import os
from urllib.parse import urlparse

def connect_db():
    try:
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            raise ValueError("DATABASE_URL not found in environment variables")

        # Parse URL
        url = urlparse(db_url)

        conn = sql.connect(
            host=url.hostname,
            user=url.username,
            password=url.password,
            database=url.path[1:],  # remove leading "/"
            port=url.port
        )
        return conn
    except Exception as e:
        print(f"Database Connection Error: {e}")
        return None


class User:
    def __init__(self, account_number, user_name, pin, email, balance=1000.00, is_admin=0):
        self.account_number = account_number
        self.user_name = user_name
        self.pin = pin
        self.balance = float(balance)
        self.email_name = email
        self.is_admin = int(is_admin)

class Operations:
    def generate_unique_account_number(self):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT account_number FROM users")
        result = cursor.fetchall()
        conn.close()

        existing_accounts = [int(row[0]) for row in result]
        if existing_accounts:
            account_number = max(existing_accounts) + 1
        else:
            account_number = 1002003000
        return account_number

    def add_user(self, email_id, account_number, user_name, pin):
        """Signup flow (opening balance 1000)."""
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (account_number, user_name, pin, balance, email, is_admin) VALUES (%s, %s, %s, %s, %s, %s)",
            (account_number, user_name, pin, 1000.00, email_id, 0)
        )
        ems.send_email_attachment(email_id, account_number, user_name, pin)
        cursor.execute(
            "INSERT INTO transactions (account_number, transaction_details, debit, credit, balance) VALUES (%s, %s, %s, %s, %s)",
            (account_number, "CREDITED- Account Opening Amount", 0, 1000, 1000)
        )
        conn.commit()
        conn.close()
        return self.login(account_number, pin)

    # ---- Admin helpers ----
    def admin_create_user(self, email_id, account_number, user_name, pin, opening_balance=1000.00, is_admin=0):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (account_number, user_name, pin, balance, email, is_admin) VALUES (%s, %s, %s, %s, %s, %s)",
            (account_number, user_name, pin, opening_balance, email_id, is_admin)
        )
        cursor.execute(
            "INSERT INTO transactions (account_number, transaction_details, debit, credit, balance) VALUES (%s, %s, %s, %s, %s)",
            (account_number, "CREDITED- Admin Opening Amount", 0, opening_balance, opening_balance)
        )
        conn.commit()
        conn.close()
        return True

    def admin_update_user(self, account_number, new_name=None, new_pin=None):
        conn = connect_db()
        cursor = conn.cursor()
        if new_name and new_pin:
            cursor.execute("UPDATE users SET user_name=%s, pin=%s WHERE account_number=%s",
                           (new_name, new_pin, account_number))
        elif new_name:
            cursor.execute("UPDATE users SET user_name=%s WHERE account_number=%s",
                           (new_name, account_number))
        elif new_pin:
            cursor.execute("UPDATE users SET pin=%s WHERE account_number=%s",
                           (new_pin, account_number))
        conn.commit()
        conn.close()
        return True

    def admin_delete_user(self, account_number):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM transactions WHERE account_number=%s", (account_number,))
        cursor.execute("DELETE FROM users WHERE account_number=%s", (account_number,))
        conn.commit()
        conn.close()
        return True

    def admin_adjust_balance(self, account_number, amount):
        """amount positive => credit, negative => debit"""
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE account_number=%s", (account_number,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return False
        current = Decimal(str(row[0]))
        new_bal = current + Decimal(str(amount))
        # Don’t let it go negative (optional rule)
        if new_bal < Decimal('0.00'):
            conn.close()
            return False

        cursor.execute("UPDATE users SET balance=%s WHERE account_number=%s", (new_bal, account_number))
        if amount >= 0:
            cursor.execute(
                "INSERT INTO transactions (account_number, transaction_details, debit, credit, balance) VALUES (%s, %s, %s, %s, %s)",
                (account_number, "CREDIT- Admin Adjustment", 0, abs(amount), new_bal)
            )
        else:
            cursor.execute(
                "INSERT INTO transactions (account_number, transaction_details, debit, credit, balance) VALUES (%s, %s, %s, %s, %s)",
                (account_number, "DEBIT- Admin Adjustment", abs(amount), 0, new_bal)
            )
        conn.commit()
        conn.close()
        return True

    def login(self, account_number, pin):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT account_number, user_name, pin, balance, email, is_admin FROM users WHERE account_number=%s AND pin=%s",
            (account_number, pin))
        result = cursor.fetchone()
        conn.close()
        if result:
            account_number, user_name, pin, balance, email, is_admin = result
            return User(account_number, user_name, pin, email, balance, is_admin)
        return None

    def forgot_pwd(self, account_num, email):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT pin FROM users WHERE account_number=%s AND email=%s", (account_num, email))
        result = cursor.fetchone()
        conn.close()
        if not result:
            return None
        subject = "OTP for Resetting PIN"
        email_text = "is your OTP for Reset PIN into Bankify App."
        return ems.otp_genrater(email, subject, email_text)

    def reset_password(self, new_pin, account_num):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET pin = %s WHERE account_number = %s", (new_pin, account_num))
        conn.commit()
        conn.close()
        return True

    def account_details(self, user):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT account_number, user_name, pin, balance, email FROM users WHERE account_number=%s",
                       (user.account_number,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return {
                "account_number": result[0],
                "name": result[1],
                # "pin": result[2],
                "balance": result[3],
                "email": result[4]
            }
        return None

    def withdraw(self, user, amount):
        from decimal import Decimal
        amount = Decimal(str(amount))
        user.balance = Decimal(str(user.balance))
        conn = connect_db()
        cursor = conn.cursor()
        if user.balance - amount >= Decimal('100.00'):
            user.balance -= amount
            cursor.execute("UPDATE users SET balance=%s WHERE account_number=%s",
                           (user.balance, user.account_number))
            cursor.execute("INSERT INTO transactions (account_number, transaction_details, debit, credit, balance) VALUES (%s, %s, %s, %s, %s)",
                           (user.account_number, "DEBIT", amount, 0, user.balance))
            conn.commit()
            conn.close()
            return f"Withdraw ₹{amount}. New balance: ₹{user.balance}"
        conn.close()
        return "Insufficient balance."

    def deposit(self, user, amount):
        from decimal import Decimal
        amount = Decimal(str(amount))
        user.balance = Decimal(str(user.balance))
        conn = connect_db()
        cursor = conn.cursor()
        user.balance += amount
        cursor.execute("UPDATE users SET balance=%s WHERE account_number=%s",
                       (user.balance, user.account_number))
        cursor.execute("INSERT INTO transactions (account_number, transaction_details, debit, credit, balance) VALUES (%s, %s, %s, %s, %s)",
                       (user.account_number, "CREDIT", 0, amount, user.balance))
        conn.commit()
        conn.close()
        return f"Deposited ₹{amount}. New balance: ₹{user.balance}"

    def check_account(self, user, recipient_account_no):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT user_name FROM users WHERE account_number = %s", (recipient_account_no,))
        result = cursor.fetchone()
        conn.close()
        return bool(result)

    def transfer(self, user, recipient_account_no, amount):
        conn = connect_db()
        cursor = conn.cursor()
        if user.account_number == recipient_account_no:
            conn.close()
            return "Cannot transfer to your own account."

        amount = Decimal(str(amount))
        user.balance = Decimal(str(user.balance))

        cursor.execute("SELECT user_name, balance FROM users WHERE account_number = %s", (recipient_account_no,))
        result = cursor.fetchone()

        if result:
            recipient_name, recipient_balance = result
            recipient_balance = Decimal(str(recipient_balance))
            if user.balance - amount >= Decimal('100.00'):
                user.balance -= amount
                recipient_balance += amount
                cursor.execute("UPDATE users SET balance=%s WHERE account_number=%s",
                               (user.balance, user.account_number))
                cursor.execute("UPDATE users SET balance=%s WHERE account_number=%s",
                               (recipient_balance, recipient_account_no))
                cursor.execute("INSERT INTO transactions (account_number, transaction_details, debit, credit, balance) VALUES (%s, %s, %s, %s, %s)",
                               (user.account_number, f"Transferred to A/C - {recipient_account_no}", amount, 0, user.balance))
                cursor.execute("INSERT INTO transactions (account_number, transaction_details, debit, credit, balance) VALUES (%s, %s, %s, %s, %s)",
                               (recipient_account_no, f"Credited from A/C - {user.account_number}", 0, amount, recipient_balance))
                conn.commit()
                conn.close()
                return f"₹{amount} Transferred to A/C - {recipient_account_no}, New balance: ₹{user.balance}"
            else:
                conn.close()
                return "Insufficient balance for transfer."
        else:
            conn.close()
            return "Recipient not found."

    def show_balance(self, user):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM users WHERE account_number=%s", (user.account_number,))
        result = cursor.fetchone()
        conn.close()
        if result:
            user.balance = result[0]
            return user.balance
        return None

    def show_transaction_history(self, user):
        conn = connect_db()
        cursor = conn.cursor()
        query = """
            SELECT * FROM (
                SELECT * FROM transactions 
                WHERE account_number = %s 
                ORDER BY id DESC 
                LIMIT 5
            ) AS tr 
            ORDER BY id ASC;
        """
        cursor.execute(query, (user.account_number,))
        records = cursor.fetchall()
        result = []
        for record in records:
            txn_time = record[6].strftime('%d-%m-%Y')
            result.append((txn_time, record[2], f"{record[3]:.2f}", f"{record[4]:.2f}", f"{record[5]:.2f}"))
        cursor.close()
        conn.close()
        return result

    def send_statement(self, user):
        conn = connect_db()
        cursor = conn.cursor()
        query = "SELECT * FROM transactions WHERE account_number = %s"
        cursor.execute(query, (user.account_number,))
        records = cursor.fetchall()
        statement = {'txn_time': [], 'txn_type': [], 'debit': [], 'credit': [], 'balance': []}
        for record in records:
            statement['txn_type'].append(record[2])
            statement['debit'].append(record[3])
            statement['credit'].append(record[4])
            statement['balance'].append(record[5])
            txn_time = record[6].strftime('%d-%m-%Y')
            statement['txn_time'].append(txn_time)

        folder_path = os.path.join(os.getcwd(), "statements")
        os.makedirs(folder_path, exist_ok=True)
        file_path = os.path.join(folder_path, f"{user.account_number}-{user.user_name}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            details = self.account_details(user)
            if details:
                f.write(
                f"Account Holder : {details['name']}\n"
                f"Account Number : {details['account_number']}\n"
                f"Email Address  : {details['email']}\n"
                f"Account Balance: ₹{details['balance']}\n"
            )
            else:
                f.write("No account details found.")
            if records:
                f.write(f"Statement From Date : {statement['txn_time'][0]}\n")
                f.write(f"Statement Till Date : {statement['txn_time'][-1]}\n")
                f.write(f"|{'-'*79}|\n")
                f.write(f"|{'DATE'.center(10)}|{'DETAILS'.center(32)}|{'DEBIT'.center(11)}|{'CREDIT'.center(11)}|{'BALANCE'.center(11)}|\n")
                f.write(f"|{'-'*79}|\n")
                for dt, dtl, dbt, crt, bal in zip(statement['txn_time'], statement['txn_type'], statement['debit'], statement['credit'], statement['balance']):
                    st = f"|{dt}|{dtl:<32}|₹{dbt:>10}|₹{crt:>10}|₹{bal:>10}|"
                    f.write(st + "\n")
                    f.write(f"|{'-'*(len(st)-2)}|\n")
            else:
                f.write("\nNo transactions found.\n")
        cursor.close()
        conn.close()
        return ems.send_account_statement(user, file_path)




