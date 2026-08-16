## Get price from db

This script read a BOM-csv that is exported from KiCad and connect to a database, mariadb, and collect price and box from the database.
Box is just the placement of the component so you know were to get it from.

The price is collected from db and multiply with the quantity of the component and the result is multipy with vat-rate.

The last row summarizes the column.

This script uses the article number from Mouser.
