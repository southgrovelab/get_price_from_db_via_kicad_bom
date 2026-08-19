#*******************************************************************************************
#                                                                                          *
# I'm not a programmer.                                                                    *
# I do this because it's fun.                                                              *
# Maybe not written in a completely correct way, but I do my best and having fun...        *
#                                                                                          *
# /Niclas                                                                                  *
#                                                                                          *
#*******************************************************************************************
#                                                                                          *
# Reads a BOM csv from KiCad, connects to a database and gets the price of the component,  *
# physical location of the component, where it is located, in which box, etc. and writes   *
# the information back to the csv file and creates a pdf document with a table of the      *
# components with total price, VAT, etc.                                                   *
#                                                                                          *
#*******************************************************************************************
#
# - Version 0.3 -
# Added list files in a directory
#
# - Version 0.4 -
# Added that it creates folders if they don't exist
#
# - Version 0.5 -
# Changed the  SQL-query to use prepared statement
# Sorted the list files in select_file()
#
# - Version 0.6 -
# Changed how the VAT is presented.
# Instead of all components having VAT added to each line, the entire line is now
# summed up and then VAT is added.
# Total excl. VAT, VAT and the total are presented on separate lines
# The total sum is rounded to the nearest tenth
# Cleaned up the code a bit
#
# - Version 0.7 -
# Added print to PDF
#
# - Version 0.8 -
# Changed the print to PDF-function
# Added footer to PDF and change some colors and make some text bold in the table
#
# - Version 0.9 -
# Added header and footer to the pdf file
# Added the ability to enter a project name or use the file name
#
#*******************************************************************************************
#
# The first time you run this script, you will get an error message that there are no
# files to load if you have not already created folder csv and another folder
# updated in the csv folder and uploaded files to the csv folder.
#
# Otherwise, run this script, upload files to the csv folder and run the script again
#
#*******************************************************************************************


import pandas as pd
import mysql.connector
import numpy as np
import credentials
import os
import csv
from pathlib import Path
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

# Create directories if they don't exist
parent_dir = "csv/"
child_dir = "updated/"
path = Path(f"{parent_dir}{child_dir}")
os.makedirs(path, exist_ok=True)

#kicad_project_name = "34"

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

# Add footer to PDF-document, page numbers and a line ***********************************************************
def add_footer(canvas, doc):
    canvas.saveState()

#Setup colors and dimensions
    line_color = colors.HexColor("#CCCCCC")  # Subtle light grey
    text_color = colors.HexColor("#666666")
    additional_text_color = colors.grey
    page_width, page_height = doc.pagesize

    left_x = 54
    right_x = page_width - 54

# Draw the horizontal line (54 points up from the bottom)
    canvas.setStrokeColor(line_color)
    canvas.setLineWidth(1)
    canvas.line(left_x, 54, right_x, 54)

# Draw the footer text (36 points up from the bottom)

    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(text_color)
    canvas.drawString(left_x, 36, f"KiCad Project Report  |  Page {doc.page} ")

    canvas.setFont("Helvetica", 10)
    canvas.setFillColor(line_color)
    canvas.drawString(left_x, page_height-36,f"Project name: {kicad_project_name}")

    canvas.restoreState()


# Select file function *******************************************************************************************
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
    print(f"************************************************** {selected} ******************************************************************")
    global kicad_project_name
    kicad_project_name = input(f"If you want to use the filename,  {os.path.splitext(selected)[0]},  as project name, just press enter otherwise type in a name: ")
    if not kicad_project_name:
        kicad_project_name = os.path.splitext(selected)[0]

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
    df = pd.read_csv(f"csv/{selected}", usecols=['Reference', 'Qty', 'Value' , 'Mouser Part. No.'])

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

# Write csv
    df.to_csv(f"{file_path_updated}{edited}{selected}", float_format='%.2f', index=False)
# Print csv in terminal
    print("")
    print(f"********************** Updated CSV-file {selected} ****************************")
    print("")
    print(df)

# Added this to print to pdf
    data = []
    with open(f"{file_path_updated}{edited}{selected}", 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            data.append(row)

    # Create PDF
    pdf = SimpleDocTemplate(f"{file_path_updated}{edited}{selected.replace('.csv','')}.pdf", pagesize=landscape(A4))
    styles = getSampleStyleSheet()

    kicad_dark_blue = colors.Color(0.19, 0.3, 0.7)
    kicad_light_blue = colors.Color(0.41, 0.64, 0.85)
    kicad_grey = colors.Color(0.03,0.03,0.03)

# Create a custom style for your title text
    title_style = ParagraphStyle(
        'ReportTitle',
        parent=styles['Heading1'],
        fontSize=26,
        leading=22,            # Always set leading slightly larger than fontSize
        textColor=kicad_dark_blue,
        spaceAfter=12          # Alternative way to add space below text
    )
    info_style = ParagraphStyle(
        'InfoTitle',
        parent=styles['Heading1'],
        fontSize=10,
        leading=22,            # Always set leading slightly larger than fontSize
        textColor=colors.HexColor('#CCCCCC'),
        spaceAfter=12          # Alternative way to add space below text
    )
    story = []

# Add the text paragraph
    title_text = Paragraph("KiCad report", title_style)
    story.append(title_text)
    info_text = Paragraph("Additional hardware such as PCB, box, etc. may be added.", info_style)
#    story.append(title_text)
    story.append(info_text)

# Add a spacer (width, height in points)
    story.append(Spacer(1, 20))


    table = Table(data)

    table.setStyle(TableStyle([
        ('FONTNAME', (-3, -3), (-1, -1), 'Helvetica-Bold'), # Bottom three row bold, Sum excl. VAT, VAT and Tot
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), # Top row bold, Reference, Qty etc.
        ('BACKGROUND', (0,0), (-1,0), kicad_light_blue),
        ('TEXTCOLOR', (0,0), (-1,0), kicad_grey),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.black),
    ]))

    story.append(table)
    pdf.build(story, onFirstPage=add_footer, onLaterPages=add_footer)


selected = select_file(file_path)

# Closing
cursor.close()
conn.close()
