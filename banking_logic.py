import email_system as ems
import random
import os
from decimal import Decimal
# from dbms import connect_db
import datetime
import mysql.connector as sql

def connect_db():
    try:
        conn = sql.connect(
            host='localhost',
            user='root',
            password='root',
            database='banking_system'
        )

    except sql.Error as e:
        print("Error while connecting to database:", e)
        return None
    else:        
        print("Connection Done db")
        return conn

class User:
    def __init__(self, account_number, user_name, pin, email):
        self.account_number = account_number
        self.user_name = user_name
        self.pin = pin
        self.balance = 1000.00
        self.email_name = email


class Operations:
    def __init__(self):
        pass

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
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (account_number, user_name, pin, email) VALUES (%s, %s, %s, %s)",
                       (account_number, user_name, pin, email_id))
        ems.send_email_attachment(email_id, account_number, user_name, pin)
        print(f"User {account_number} - {user_name} created successfully.")

        cursor.execute("INSERT INTO transactions (account_number, transaction_details, debit, credit, balance) VALUES (%s, %s, %s, %s, %s)",
                       (account_number, "CREDITED- Account Opening Amount", 0, 1000, 1000))
        conn.commit()
        conn.close()

        user = self.login(account_number, pin)
        return user

    def login(self, account_number, pin):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT account_number, user_name, pin, balance, email FROM users WHERE account_number=%s AND pin=%s",
            (account_number, pin))
        result = cursor.fetchone()
        conn.close()
        if result:
            account_number, user_name, pin, balance, email = result
            user = User(account_number, user_name, pin, email)
            user.balance = float(balance)
            print(f"User {user.user_name} login successful.")
            return user
        else:
            print("USER NOT FOUND")
            return None

    def forgot_pwd(self, account_num, email):
        conn = connect_db()
        cursor = conn.cursor()
        cursor.execute("SELECT pin FROM users WHERE account_number=%s AND email = %s", (account_num, email))
        result = cursor.fetchone()

        if not result:
            conn.close()
            return
        conn.close()
        subject = "OTP for Resetting PIN"
        email_text = "is your OTP for Reset PIN into Banking System."
        otp = ems.otp_genrater(email, subject, email_text)
        return otp

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
            user_name = result[1]
            user_account_number = result[0]
            user_pin = result[2]
            user_balance = result[3]
            user_email_id = result[4]
            return (f"""
Account Holder : {user_name}
Account Number : {user_account_number}
Email Address  : {user_email_id}
Login Password : {user_pin}
Account Balance: ₹{user_balance}
""")
        else:
            print("USER NOT FOUND")

    def withdraw(self, user, amount):
        print(user)
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
        else:
            return "Insufficient balance."

    def deposit(self, user, amount):
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
    def check_account (self, user, recipient_account_no):
        conn = connect_db()
        cursor = conn.cursor()

        # if user.account_number == recipient_account_no:
            # conn.close()
            # return "Cannot transfer to your own account."

        # amount = Decimal(str(amount))
        # user.balance = Decimal(str(user.balance))

        cursor.execute("SELECT user_name, balance FROM users WHERE account_number = %s", (recipient_account_no,))
        result = cursor.fetchone()
        if result:
            return True
        else:
            return False

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
                               (user.account_number, f"Transferred to A/C - {recipient_account_no}", amount, 0,
                                user.balance))
                cursor.execute("INSERT INTO transactions (account_number, transaction_details, debit, credit, balance) VALUES (%s, %s, %s, %s, %s)",
                               (recipient_account_no, f"Credited from A/C - {user.account_number}", 0, amount,
                                recipient_balance))

                conn.commit()
                conn.close()

                print(f"₹{amount} Transferred to A/C - {recipient_account_no}, New balance: ₹{user.balance}")
                print(f"₹{amount} Received from A/C - {user.account_number}, New balance: ₹{recipient_balance}")
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
            # return f"Current Balance: ₹{user.balance}"
            return user.balance
        else:
            return None

    def show_transaction_history(self, user):
        conn = connect_db()
        cursor = conn.cursor()
        account_number = user.account_number
        query = """
            SELECT * FROM (
                SELECT * FROM transactions 
                WHERE account_number = %s 
                ORDER BY id DESC 
                LIMIT 5
            ) AS tr 
            ORDER BY id ASC;
        """
        cursor.execute(query, (account_number,))
        records = cursor.fetchall()

        result = []
        for record in records:
            txn_type = record[2]
            debit = f"{record[3]:.2f}"
            credit = f"{record[4]:.2f}"
            balance = f"{record[5]:.2f}"
            txn_time = record[6].strftime('%d-%m-%Y')
            result.append((txn_time, txn_type, debit, credit, balance))

        cursor.close()
        conn.close()
        return result

    # def send_statement(self, user):
    #     conn = connect_db()
    #     cursor = conn.cursor()
    #     account_number = user.account_number
    #     query = """
    #         SELECT * FROM transactions 
    #             WHERE account_number = %s;
    #     """
    #     cursor.execute(query, (account_number,))
    #     records = cursor.fetchall()

    #     statement = {'txn_time': [], 'txn_type': [], 'debit': [], 'credit': [], 'balance': []}
    #     for record in records:
    #         statement['txn_type'].append(record[2])
    #         statement['debit'].append(record[3])
    #         statement['credit'].append(record[4])
    #         statement['balance'].append(record[5])
    #         txn_time = record[6]
    #         txn_time = txn_time.strftime('%d-%m-%Y')
    #         statement['txn_time'].append(txn_time)

    #     date1, details1, debit1, credits1, balance1 = statement.values()

    #     folder_path = os.path.expanduser("~/Desktop/vs_code_projects/banking_system/bank_statements")
    #     os.makedirs(folder_path, exist_ok=True)

    #     file_path = os.path.join(folder_path, f"{account_number}-{user.user_name}.txt")
    #     f = open(file_path, "w")
    #     print(file_path)

    #     user_detail = self.account_details(user)
    #     f.write(user_detail)
    #     f.write(f"Statement From Date : {statement['txn_time'][0]}\n")
    #     f.write(f"Statement Till Date : {statement['txn_time'][-1]}\n")
    #     f.write(f"|{'-'.center(79, '-')}|\n")
    #     f.write(f"|{'DATE'.center(10, '-')}|{'DETAILS'.center(32, '-')}|{'DEBIT'.center(11, '-')}|{'CREDIT'.center(11, '-')}|{'BALANCE'.center(11, '-')}|\n")
    #     f.write(f"|{'-'.center(79, '-')}|\n")

    #     for dt, dtl, dbt, crt, bal in zip(date1, details1, debit1, credits1, balance1):
            # st = f"|{dt}|{dtl:<32}|₹{dbt:>10}|₹{crt:>10}|₹{bal:>10}|"
    #         f.write(f"{st}\n")
    #         f.write(f"|{'-'.center(len(st) - 2, '-')}|\n")
    #         print(st)
    #         print(f"|{'-'.center(len(st) - 2, '-')}|")

    #     result = ems.send_account_statement(user, file_path)
    #     cursor.close()
    #     conn.close()
        # f.close()
        # return result


    def send_statement(self,user):
        conn = connect_db()
        cursor = conn.cursor()
        account_number = user.account_number  #  user's account number
        query = """
            SELECT * FROM transactions 
                WHERE account_number = %s;
        """
        cursor.execute(query, (account_number,))
        records = cursor.fetchall()

        # records_str = f"Last 5 Transactions for Account {account_number}:\n\n"
        statement = {'txn_time': [], 'txn_type': [],'debit':[], 'credit': [], 'balance': [] }
        for record in records:
            # transaction_id = record[0]
            # acc_no = record[1]
            statement['txn_type'].append(record[2])
            statement['debit'].append(record[3])
            statement['credit'].append(record[4])
            statement['balance'].append(record[5])
            txn_time = record[6]
            txn_time = txn_time.strftime('%d-%m-%Y')
            statement['txn_time'].append(txn_time)
               
        date1, details1, debit1, credits1, balance1 = statement.values()

        # Expand path and ensure directory exists
        # folder_path = os.path.expanduser("~/Desktop/vs_code_projects/banking_system/bank_statements")
        # os.makedirs(folder_path, exist_ok=True) # make directrory if it not exist
        # file_path = os.path.join(folder_path, f"{account_number}-{user.user_name}.txt")
        # # file_path = "~/Desktop/vs_code_projects/banking_system/bank_statements/{account_number}-{user.user_name}.txt"
        # f = open(f"~/Desktop/vs_code_projects/banking_system/bank_statements/{account_number}-{user.user_name}.txt", "w")
        # Create directory if not exists

        # folder_path = os.path.expanduser("~/Desktop/vs_code_projects/banking_system/bank_statements")
        folder_path = os.path.expanduser(r"C:\Users\Dell\Desktop\bank_statements")
        os.makedirs(folder_path, exist_ok=True)

        # Correctly expand and create the file path
        file_path = os.path.join(folder_path, f"{account_number}-{user.user_name}.txt")
        # f = open(file_path, "w")
        f = open(file_path, "w", encoding="utf-8")

        user_detail = self.account_details(user)
        f.write(user_detail)
        f.write(f"Statement From Date : {statement['txn_time'][0]}\n")
        f.write(f"Statement Till Date : {statement['txn_time'][-1]}\n")
        f.write(f"|{'-'.center(79,'-')}|\n")
        f.write(f"|{'DATE'.center(10, '-')}|{'DETAILS'.center(32, '-')}|{'DEBIT'.center(11, '-')}|{'CREDIT'.center(11, '-')}|{'BALANCE'.center(11, '-')}|\n")
        f.write(f"|{'-'.center(79,'-')}|\n")

        print(f"|{'-'.center(79,'-')}|")
        print(f"|{'DATE'.center(10, '-')}|{'DETAILS'.center(32, '-')}|{'DEBIT'.center(11, '-')}|{'CREDIT'.center(11, '-')}|{'BALANCE'.center(11, '-')}|")
        print(f"|{'-'.center(79,'-')}|")
        
        for dt, dtl, dbt,crt,bal in zip(date1, details1, debit1, credits1, balance1):
            dt = str(dt)
            dtl= str(dtl)
            dbt = str(dbt)
            crt = str(crt)
            bal = str(bal)
            st = f"|{dt}|{dtl:<32}|₹{dbt:>10}|₹{crt:>10}|₹{bal:>10}|"
            f.write(f"{st}\n")       
            f.write(f"|{'-'.center(len(st)-2,'-')}|\n")
              
            print(st)
            print(f"|{'-'.center(len(st)-2,'-')}|")
        
        else:
            f.close()
        result = ems.send_account_statement(user,file_path)
        cursor.close()
        conn.close()
        f.close()
        return result

    def extra_data():
        pass


def main():
    opt = Operations()


if __name__ == "__main__":
    main()
