import tkinter as tk
from tkinter import ttk
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
from PIL import Image, ImageTk
from tkinter import messagebox, simpledialog
from email_system import otp_genrater, send_email_attachment
# from dbms import connect_db
from decimal import Decimal, InvalidOperation
from banking_logic import Operations, User
from tkinter import Toplevel
import mysql.connector as sql


# root window
root = tk.Tk()
root.title("Banking Application")
root.geometry("650x550")
root.configure(bg="#e6f2ff")  # Light blue background

'''
# Load the image
image = Image.open("bgimg.jpg")  # Change to your image path
image = image.resize((640, 540))  # Resize to match window
bg_image = ImageTk.PhotoImage(image)

# Create a label to hold the background image
bg_label = tk.Label(root, image=bg_image)
bg_label.place(x=0, y=0, relwidth=1, relheight=1)
'''

# # Create main window
# root = tk.Tk()
# root.title("Banking System - Login")
# # root.geometry("900x600")
# root.geometry("650x550")
# root.resizable(False, False)
# root.configure(bg="red")

# Load and set background image
# bg_image = Image.open("bgimg.jpg")  # <-- Replace with your image path
# bg_image = bg_image.resize((900, 600))
# bg_photo = ImageTk.PhotoImage(bg_image)

# bg_label = tk.Label(root, image=bg_photo)
# bg_label.place(x=0, y=0, relwidth=1, relheight=1)



opt = Operations()
current_user = None
balance_limit = 99999999.99 # 10 carod - 0.1 

def transaction_history_table(data):
    win = tk.Toplevel()
    win.title("Last 5 Transactions History")
    win.geometry("800x300")
    win.configure(bg="#f0f4f7")

    style = ttk.Style()
    # style.theme_use("clam")
    style.configure("Treeview",
                    background="white",
                    foreground="black",
                    rowheight=30,
                    fieldbackground="white",
                    font=("Segoe UI", 10))
    style.map("Treeview",
              background=[("selected", "#4a7abc")],
              foreground=[("selected", "white")])

    tree = ttk.Treeview(win, columns=("Date", "Details", "Debit", "Credit", "Balance"), show="headings")
    headings = ["Date", "Details", "Debit (₹)", "Credit (₹)", "Balance (₹)"]
    for col, text in zip(tree["columns"], headings):
        tree.heading(col, text=text)
        tree.column(col, anchor="center", width=150 if col == "Details" else 100)

    # Add alternating row colors
    tree.tag_configure('oddrow', background="#e7f0fd")
    tree.tag_configure('evenrow', background="#ffffff")

    for i, row in enumerate(data):
        tag = 'oddrow' if i % 2 == 0 else 'evenrow'
        tree.insert("", "end", values=row, tags=(tag,))

    scrollbar = ttk.Scrollbar(win, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    tree.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
    scrollbar.grid(row=0, column=1, sticky="ns", pady=10)

    win.grid_rowconfigure(0, weight=1)
    win.grid_columnconfigure(0, weight=1)

    win.mainloop()



def clear_screen():
    for widget in root.winfo_children():
        widget.destroy()

def show_main_menu():
    clear_screen()
    tk.Label(root, text=f"Welcome {current_user.user_name}", font=("Arial", 14)).pack(pady=10)

    ttkb.Button(root, text="Transactions History", command=show_transaction_history, bootstyle=INFO).pack(pady=5)
    ttkb.Button(root, text="Send Statement on Email", command=send_email_statement, bootstyle=INFO).pack(pady=5)
    ttkb.Button(root, text="Withdraw", command=withdraw_amount, bootstyle=INFO).pack(pady=5)
    ttkb.Button(root, text="Deposit", command=deposit_amount, bootstyle=INFO).pack(pady=5)
    ttkb.Button(root, text="Transfer", command=transfer_amount, bootstyle=INFO).pack(pady=5)
    ttkb.Button(root, text="Check Balance", command=check_balance, bootstyle=INFO).pack(pady=5)
    ttkb.Button(root, text="Account Details", command=account_details, bootstyle=INFO).pack(pady=5)
    ttkb.Button(root, text="Logout", command=show_login_menu, bootstyle=DANGER).pack(pady=20)

def chech_db():
    try:
        conn = sql.connect(
            host='localhost',
            user='root',
            password='root',
            # database='banking_system'
        )
        cursor = conn.cursor()
        query_showdb = "show databases"
        cursor.execute(query_showdb)
        if ("banking_system",) in cursor.fetchall():
            return "database already exists"
        else:
            cursor = conn.cursor()
            query_dbname = "create database if not exists banking_system"
            cursor.execute(query_dbname)

            cursor = conn.cursor()
            query_usedb = "use banking_system"
            cursor.execute(query_usedb)
            conn.commit()   

    except sql.Error as e:
        print("Error while connecting to database gui message:", e)
        return None
    else: 
        # print("Connection Done gui message")
        try:
            # return conn
            cursor = conn.cursor()
            
            query = """CREATE TABLE IF NOT EXISTS users (
    account_number VARCHAR(20) NOT NULL PRIMARY KEY,
    user_name VARCHAR(100),
    pin VARCHAR(20),
    balance DECIMAL(10,2) DEFAULT 1000.00,
    email VARCHAR(100)
);"""
            cursor.execute(query)
            query2 = """CREATE TABLE IF NOT EXISTS transactions (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    account_number VARCHAR(20),
    transaction_details VARCHAR(100),
    debit DECIMAL(10,2),
    credit DECIMAL(10,2),
    balance DECIMAL(10,2),
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);"""
            cursor.execute(query2)
            conn.commit()
        except Exception as e:
            print(e)
        else:
            return "database created"
        

def show_login_menu():
    clear_screen()
    # pass 
    tk.Label(root, text="Bank Login", font=("Arial", 16)).pack(pady=20)
    
    tk.Label(root, text="Account Number").pack()
    acc_entry = ttkb.Entry(root, bootstyle="primary")
    acc_entry.pack(pady=5)

    tk.Label(root, text="PIN").pack()
    pin_entry = ttkb.Entry(root, show="*", bootstyle="primary")
    pin_entry.pack(pady=5)

    # Add a Progressbar (initially not moving)
    progress = ttkb.Progressbar(root, bootstyle="info-striped", mode="determinate", length=150)
    progress.pack(pady=15)
    progress["value"] = 10
    

    def login():
        global current_user
        acc = acc_entry.get().strip()
        pin = pin_entry.get().strip()

        if not acc or not pin:
            messagebox.showwarning("Input Error", "Please enter both account number and PIN.")
            progress.stop()
            return

        user = opt.login(acc, pin)
        progress.stop()

        if user:
            current_user = user
            show_main_menu()
        else:
            messagebox.showerror("Login Failed", "Invalid credentials")

    def on_login():
        progress.start(10)  # Starts animation
        root.after(1000, login)  # Calls login after 1 seconds (simulate delay)

    # Buttons
    ttkb.Button(root, text="Login", command=on_login, bootstyle=SUCCESS).pack(padx=5, pady=10)
    ttkb.Button(root, text="Sign Up", command=show_signup, bootstyle=PRIMARY).pack(padx=5, pady=10)
    ttkb.Button(root, text="Forgot PIN", command=forgot_reset_pwd, bootstyle=DANGER).pack(padx=5)

def show_signup():
    clear_screen()
    tk.Label(root, text="Sign Up", font=("Arial", 16)).pack(pady=10)

    tk.Label(root, text="Email ID").pack()
    email_entry = ttkb.Entry(root, bootstyle="primary")
    email_entry.pack()

    tk.Label(root, text="User Name").pack()
    name_entry = ttkb.Entry(root, bootstyle="primary")
    name_entry.pack()

    tk.Label(root, text="PIN").pack()
    pin_entry = ttkb.Entry(root, show="*", bootstyle="primary")
    pin_entry.pack()

    def submit_signup():
        global current_user
        email = email_entry.get().strip()
        name = name_entry.get().strip().title()
        pin = pin_entry.get().strip()

        if not email or not name or not pin:
            messagebox.showwarning("Input Error", "All fields are required.")
            return

        if not email.endswith(".com"):
            messagebox.showerror("Error", "Enter a valid email.")
            return
        subject = "OTP for Create New Account into Banking System"
        email_text = "is your OTP for Sign up into Banking System."
        otp = otp_genrater(email,subject,email_text)
        if otp:
            entered_otp = simpledialog.askstring("OTP", "Enter OTP sent to your email:")
            # if type(entered_otp) == str:
            #     messagebox.showwarning("Invalid Input", "Please enter correct OTP.")
            #     return
            # elif entered_otp is None:
            #     return
            
            if type(entered_otp) == str and len(entered_otp) == 0:
                messagebox.showwarning("Invalid OTP", "Please Enter Valid OTP.")
                return
            elif entered_otp is None:
                return
            elif str(otp) != str(entered_otp).strip():
                messagebox.showerror("Error", "OTP verification failed.")
                return
        else:
            messagebox.showerror("Error", "Email Address Not Found.")
            return

        if entered_otp is None or str(otp) != str(entered_otp).strip():
            messagebox.showerror("Error", "OTP verification failed.")
            return

        account_number = opt.generate_unique_account_number()
        user = opt.add_user(email, account_number, name, pin)
        if user:
            messagebox.showinfo("Success", f"Account created. Your account number is {account_number}")
            current_user = user
            show_main_menu()
    
    ttkb.Button(root, text="Register", command=submit_signup, bootstyle=SUCCESS).pack(pady=10)
    ttkb.Button(root, text="Back to Login", command=show_login_menu, bootstyle=WARNING).pack()

def forgot_reset_pwd():
    clear_screen()
    tk.Label(root, text="Reset PIN", font=("Arial", 16)).pack(pady=10)

    tk.Label(root, text="Enter your Account Number").pack()
    account_num_entry = ttkb.Entry(root, bootstyle="primary")
    account_num_entry.pack()

    tk.Label(root, text="Enter your registered Email ID").pack()
    email_entry = ttkb.Entry(root, bootstyle="primary")
    email_entry.pack()

    def send_reset_otp():
        account_num = account_num_entry.get().strip()
        email = email_entry.get().strip()

        if not account_num:
            messagebox.showwarning("Invalid Account Number", "Please enter Account Number.")
            return

        if not email or not email.endswith(".com"):
            messagebox.showwarning("Invalid Email", "Please enter a valid email address.")
            return

        otp = opt.forgot_pwd(account_num, email)
        if not otp:
            messagebox.showerror("Error", "No user found with these details.")
            return

        entered_otp = simpledialog.askstring("OTP", "Enter OTP sent to your email:")

        #if entered_otp is None :
        if type(entered_otp) == str and len(entered_otp) == 0:
            messagebox.showwarning("Invalid OTP", "Please Enter Valid OTP.")
            return
        elif entered_otp is None:
            return
        elif str(otp) != str(entered_otp).strip():
            messagebox.showerror("Error", "OTP verification failed.")
            return

        new_pin = simpledialog.askstring("New PIN", "Enter new PIN:", show="*")

        if not new_pin or len(new_pin.strip()) < 4:
            messagebox.showwarning("Invalid", "PIN should be at least 4 digits.")
            return

        result = opt.reset_password(new_pin.strip(), account_num)
        if result:
            messagebox.showinfo("Success", "NEW PIN set successfully.")
            show_login_menu()
        else:
            messagebox.showerror("Error", "Something went wrong.")

    ttkb.Button(root, text="Send OTP & Reset PIN", command=send_reset_otp, bootstyle=SUCCESS).pack(pady=10)
    ttkb.Button(root, text="Back to Login", command=show_login_menu, bootstyle=WARNING).pack()


def withdraw_amount():
    input_str = simpledialog.askstring("Withdraw", "Enter amount to withdraw:")
    # print(type(input_str))


    if type(input_str) == str and len(input_str) == 0:
        messagebox.showwarning("Invalid Input", "Please enter some amount.")
        return
    elif input_str is None:
        return
    
    try:
        amount = float(input_str)
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a valid number.")
        return

    if amount <= 0:
        messagebox.showerror("Invalid Input", "Amount should be greater than zero.")
    else:
        trs = opt.withdraw(current_user, amount)
        if 'Withdraw' in trs:
            messagebox.showinfo("Success", trs)
        else:
            messagebox.showwarning("Failed", trs)

def deposit_amount():
    input_str = simpledialog.askstring("Deposit", "Enter amount to deposit:")  

    balance  = opt.show_balance(current_user) # fetch current balance


    if type(input_str) == str and len(input_str) == 0:
        messagebox.showwarning("Invalid Input", "Please enter some amount.")
        return
    elif input_str is None:
        return

    try:
        amount = float(input_str)
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a valid number.")
        return
    if amount is None:
        messagebox.showwarning("Invalid Input", "Please enter some amount.")
    elif amount <= 0:
        messagebox.showerror("Invalid Input", "Amount should be greater than zero.")
    elif amount + float(balance) > balance_limit:
        messagebox.showwarning("Invalid Input", "Account Balance Limit is only ₹99999999.99")
    else:
        result = opt.deposit(current_user, amount)
        messagebox.showinfo("Success", result)

def transfer_amount():
    recipient = simpledialog.askstring("Transfer", "Enter recipient account number:")
    if type(recipient) == str and len(recipient) == 0 :
        messagebox.showwarning("Invalid Input", "Please enter valid recipient.")
        return
    elif recipient is None:
        return
    elif type(recipient) == str and len(recipient) != 0:
        if current_user.account_number == recipient:
            messagebox.showwarning('SAME ACCOUNT',"Cannot transfer to your own account.")
            return
        elif opt.check_account(current_user, recipient) == False:
            messagebox.showwarning("Invalid Input", "Recipient account Number is not valid.")
            return

    
    # if not recipient:
    #     messagebox.showwarning("Invalid Input", "Please enter valid recipient.")
    #     return
    
    input_str = simpledialog.askstring("Transfer", "Enter amount to transfer:")
    
    if type(input_str) == str and len(input_str) == 0:
        messagebox.showwarning("Invalid Input", "Please enter some amount.")
        return
    elif input_str is None:
        return

    try:
        amount = float(input_str)
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a valid number.")
        return
    
    if amount is None:
        messagebox.showwarning("Invalid Input", "Please enter some amount.")
    elif amount <= 0:
        messagebox.showerror("Invalid Input", "Amount should be greater than zero.")
    else:
        result = opt.transfer(current_user, recipient, amount)
        if "Cannot transfer" in result:
            messagebox.showerror("Error", result)
        elif "Transferred to" in result:
            messagebox.showinfo("Success", result)
        elif "Insufficient balance" in result:
            messagebox.showwarning("Insufficient Balance", result)
        else:
            messagebox.showerror("Error", result)


def check_balance():
    balance = opt.show_balance(current_user)
    if balance:
        messagebox.showinfo("Balance",f"Current Balance: ₹{balance}")
    else:
        messagebox.showerror("Error","Unable to fetch Balance for this Account Number")


def show_account_messagebox(title, message):
    top = Toplevel()
    top.title(title)
    top.geometry("500x200")  # Width x Height
    top.resizable(False, False)

    label = tk.Label(top, text=message, font=("Arial", 12), wraplength=420,justify='left')
    label.pack(pady=10)

    ok_button = tk.Button(top, text="OK", command=top.destroy, font=("Arial", 10))
    ok_button.pack(pady=10)

    top.grab_set()  # Modal behavior
    top.mainloop()

def show_transaction_messagebox(title, message):
    top = Toplevel()
    top.title(title)
    top.geometry("900x400")  # Width x Height
    top.resizable(False, False)

    label = tk.Label(top, text=message, font=("Arial", 12), wraplength=420,justify='left')
    label.pack(pady=10)

    ok_button = tk.Button(top, text="OK", command=top.destroy, font=("Arial", 10))
    ok_button.pack(pady=10)

    top.grab_set()  # Modal behavior
    top.mainloop()


def account_details():
    details = opt.account_details(current_user)
    show_account_messagebox("Account Details", details)
    # messagebox.showinfo("Account Details", details)



def send_email_statement():
    result = opt.send_statement(current_user)
    if result:
        messagebox.showinfo("Success","Statement has been sent to your email")
        return
    else:
        messagebox.showerror("ERROR","Something went wrong")
        return


def show_transaction_history():
    formatted_details = opt.show_transaction_history(current_user)  # now returns list of tuples

    if formatted_details:
        transaction_history_table(formatted_details)
    else:
        messagebox.showinfo("Transaction History", "No transactions found.")

        

# Start with login
res = chech_db()
print(res)
show_login_menu()
# login()
root.mainloop()