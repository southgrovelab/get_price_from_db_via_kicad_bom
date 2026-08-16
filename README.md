### Get price from db ###
This script read a BOM-csv that is exported from KiCad and connect to a database, mariadb, and collect price and box from the database. Box is just the placement of the component so you know were to get it from.

The price is collected from db and multiply with the quantity of the component and the result is multipy with vat-rate.

The last row summarizes the column.

This script uses the article number from Mouser.

## Example on a csv-file before ##  
Reference,Qty,Value,DNP,Exclude from BOM,Exclude from Board,Footprint,Mouser Part. No.
"C3,C20,C21,C22,C23,C24,C25,C26,C27,C29",11,100n,,,,Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder,77-VJ0603Y104JXQPBC 

## Example on a csv-file after ##
Reference,Qty,Value,DNP,Exclude from BOM,Exclude from Board,Footprint,Mouser Part. No.,Box,Price,Tot price ,Tot price incl VAT
"C3,C20,C21,C22,C23,C24,C25,C26,C27,C29",11.00,100n,,,,Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder,77-VJ0603Y104JXQPBC,***3,1.54,16.94,21.18***
