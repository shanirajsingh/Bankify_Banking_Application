# import mysql.connector as sql

# def connect_db():
#     try:
#         conn = sql.connect(
#             host='localhost',
#             user='root',
#             password='root',
#             database='banking_system'
#         )

#     except sql.Error as e:
#         print("Error while connecting to database:", e)
#         return None
#     else:        
#         print("Connection Done db")
#         return conn
    

# #add statement , add change pin , try to run on multiple users and ,machines
# # last change ui ,SELECT * FROM transactions WHERE account_number = 2708963508ORDER BY transaction_time DESC LIMIT 5
