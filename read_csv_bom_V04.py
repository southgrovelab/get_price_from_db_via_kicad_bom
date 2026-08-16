#***************************************************************************************
# I'm not a programmer.                                                                *
# I do this because it's fun.                                                          *
# Maybe not written in a completely correct way, but I do my best and having fun...    *
#                                                                                      *
#***************************************************************************************
#
# Read a BOM-csv from KiCad and get the price of the component, 
# physical location of the component, 
# where it is located, in which box, etc.
#
# Version 0.3
# Added list files in a directory
#
# Version 0.4
# Added that it creates folders if they don't exist
#
#********************************************************************

import pandas as pd
import mysql.connector
import numpy as np
import credentials
import os
from pathlib import Path
#from file_selector import select_file

# Create directories if they don't exist
parent_dir = "csv/"
child_dir = "updated/"
path = Path(f"{parent_dir}{child_dir}")
os.makedirs(path, exist_ok=True)


file_path = f"{parent_dir}/" # File path to the csv-files
file_path_updated = f"{parent_dir}{child_dir}" # Path to the directory where the updated files are saved

# SQL-connection
conn = mysql.connector.connect(
    host=credentials.DB_HOST,
    user=credentials.DB_USER,
    password=credentials.DB_PASS,
    database=credentials.DB_NAME
)
cursor = conn.cursor()

# Select file function
def select_file(directory):
    # List only files (excluding subdirectories)
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]

    if not files:
        print("No files found.")
        return None

    # Display numbered list
    for i, file in enumerate(files, 1):
        print(f"[{i}] {file}")

    # Get user choice
    try:
        choice = int(input("Select file number: "))
        if 1 <= choice <= len(files):
            process_sql(files[choice -1])
        else:
            print("Invalid selection.")
            return None
    except ValueError:
        print("Please enter a valid number.")
        return None
#**********************************************************************


def process_sql(selected):
#    selected = select_file("../csv/")

# Set vat
    vat = 1.25

    box_list = []
    price_per_piece = []
    tot_price = []
    tot_price_incl_vat = []
    edited = "updated_file_" # Text before after the filename when the file is edited

# Set display precision globally for the session
    pd.options.display.float_format = '{:.2f}'.format

# Read only the 'column_name' column
    df = pd.read_csv(f"../csv/{selected}")

# Access the column as a Series or list
    column_mouser = df['Mouser Part. No.']
    column_qty = df['Qty']

# SQL-Query
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
            tot_price_incl_vat.append(float(row[0][1])*(float(quantity))*vat)


    df['Box'] = np.array(box_list)
    df['Price'] = np.round(np.array(price_per_piece),2)
    df['Tot price '] = np.round(np.array(tot_price),2)
    df['Tot price incl VAT'] = np.round(np.array(tot_price_incl_vat),2)
    df.loc['Total']= pd.Series(round(df['Tot price incl VAT'].sum(),2), index=['Tot price incl VAT'])
    df.to_csv(f"{file_path_updated}{edited}{selected}", float_format='%.2f', index=False)
    print("")
    print("********************** Updated CSV-file ****************************")
    print("")
    print(df)


selected = select_file(file_path)

cursor.close()
conn.close()
