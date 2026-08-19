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
# Version 0.5
# Changed the  SQL-query to use prepared statement
# Sorted the list files in select_file()
#
# Version 0.6
# Changed how the VAT is presented.
# Instead of all components having VAT added to each line, the entire line is now summed up and then VAT is added.
# Total excl. VAT, VAT and the total are presented on separate lines
# The total sum is rounded to the nearest tenth
# Cleaned up the code a bit
#
#********************************************************************
#
# The first time you run this script, you will get an error message that there are no files to load
# if you have not already created folder csv and another folder 
# updated in the csv folder and uploaded files to the csv folder.
#
# Otherwise, run this script, upload files to the csv folder and run the script again



import pandas as pd
import mysql.connector
import numpy as np
import credentials
import os
from pathlib import Path


# Create directories if they don't exist
parent_dir = "csv/"
child_dir = "updated/"
path = Path(f"{parent_dir}{child_dir}")
os.makedirs(path, exist_ok=True)

# File path to the csv-files
file_path = f"{parent_dir}/"
# Path to the directory where the updated files are saved
file_path_updated = f"{parent_dir}{child_dir}"

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
    files.sort()
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

# Set vat
    vat = 1.25

# Set lists
    box_list = []
    price_per_piece = []
    tot_price = []

# Text that is added before the original filename when the edited file is saved
    edited = "updated_file_" 

# Set display precision globally for the session
    pd.options.display.float_format = '{:.2f}'.format

# Read the csv-file
    df = pd.read_csv(f"csv/{selected}")

# Access the columns
    column_mouser = df['Mouser Part. No.']
    column_qty = df['Qty']

# SQL-Query
    for mouser_no, quantity in zip(column_mouser, column_qty):
        if pd.isna(mouser_no):
            mouser_no = None
        sql_query = "SELECT box, price FROM tbl_stock_components_2 WHERE supplier_part_number= %s"
        data = (mouser_no,)
        cursor.execute(sql_query, data)
        row = cursor.fetchall()
        if not row:
            box_list.append("No Data")
            price_per_piece.append(0.00)
            tot_price.append(0.00)
        else:
            box_list.append(row[0][0])
            price_per_piece.append(float(row[0][1])) # Populate price to list
            tot_price.append(float(row[0][1])*(float(quantity))) # The list is populated with price times quantity of the component type.

# Prepare to write csv
    df['Box'] = np.array(box_list)
    df['Price'] = np.round(np.array(price_per_piece),2)
    df['Tot price'] = np.round(np.array(tot_price),2)

    sum_excl_vat = round(df['Tot price'].sum(), 2)
    vat = (sum(tot_price) * 0.25)
    tot = np.round(sum(tot_price) * 1.25, 1) # Round the number to the nearest tenth
#    tot = sum(tot_price) * 1.25 # If you don't want to round anything, uncomment this line and comment the line above

    summary_rows = pd.DataFrame([
        {'Box': 'Sum excl. VAT', 'Tot price': sum_excl_vat},
        {'Box': 'VAT',           'Tot price': vat},
        {'Box': 'Tot',           'Tot price': tot},
    ])

    df = pd.concat([df, summary_rows], ignore_index=True)


#    df.loc['Sum excl. VAT'] = pd.Series(round(df['Tot price'].sum(),2), index=['Tot price'])
#    df.loc['VAT']=pd.Series((sum(tot_price)*0.25), index=['Tot price'])
#    df.loc['Tot']=pd.Series((round(sum(tot_price)*1.25)), index=['Tot price'])
# Write csv
    df.to_csv(f"{file_path_updated}{edited}{selected}", float_format='%.2f', index=False)
# Print csv in terminal
    print("")
    print(f"********************** Updated CSV-file {selected} ****************************")
    print("")
    print(df)


selected = select_file(file_path)

# Closing
cursor.close()
conn.close()
