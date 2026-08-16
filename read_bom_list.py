import pandas as pd
import mysql.connector
import numpy as np
import credentials

# Use credentials from credentials to connect to db
conn = mysql.connector.connect(
    host=credentials.DB_HOST,
    user=credentials.DB_USER,
    password=credentials.DB_PASS,
    database=credentials.DB_NAME
)
cursor = conn.cursor()

def process_sql():
# Set vat
    vat_rate = 1.25

# Set lists
    box_list = [] # Where components are physically located
    price_per_piece = [] # Price of components per piece
    tot_price = [] # Component price per piece times the number of components used in the circuit
    tot_price_incl_vat = [] # tot_price times vat_rate

# Set display precision globally for the session
    pd.options.display.float_format = '{:.2f}'.format

# Read csv
# Hardcoded now, will become more dynamic
    df = pd.read_csv('/home/niclas/KiCad_Projects/Vedtimer/csv/vedtimer.csv')

# Access the column_mouser and column_qty
    column_mouser = df['Mouser Part. No.']
    column_qty = df['Qty']

#print(Connect to db and get mouser_no and quantity)
    for mouser_no, quantity in zip(column_mouser, column_qty):
        cursor.execute(f"SELECT box, price FROM tbl_stock_components_2 WHERE supplier_part_number='{mouser_no}'")
        row = cursor.fetchall()
        if not row:
            box_list.append("No Data")
            price_per_piece.append(0.00)
            tot_price.append(0.00)
            tot_price_incl_vat.append(0.00)
        else:
            box_list.append(row[0][0])
            price_per_piece.append(float(row[0][1]))
            tot_price.append(float(row[0][1])*(float(quantity)))
            tot_price_incl_vat.append(float(row[0][1])*(float(quantity))*vat_rate)

# Prepare to write to csv
    df['Box'] = np.array(box_list)
    df['Price'] = np.round(np.array(price_per_piece),2)
    df['Tot price '] = np.round(np.array(tot_price),2)
    df['Tot price incl VAT'] = np.round(np.array(tot_price_incl_vat),2)
    df.loc['Total']= pd.Series(round(df['Tot price incl VAT'].sum(),2), index=['Tot price incl VAT'])

# Write to csv
    df.to_csv("/home/niclas/KiCad_Projects/Vedtimer/csv/vedtimer.csv", float_format='%.2f', index=False)

# Print csv to terminal
    print("")
    print("********************** Updated CSV-file ****************************")
    print("")
    print(df)

process_sql()

cursor.close()
conn.close()
