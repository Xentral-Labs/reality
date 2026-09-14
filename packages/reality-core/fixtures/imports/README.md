# File import demo set

These small files exercise every explicit file-mapping profile. They form one
coherent tenant story and may be used manually in **System → Import data** or by
automated tests.

Import into an empty tenant in this order:

1. `01_parties.csv` as **Parties**
2. `02_locations.csv` as **Locations**
3. `03_items.csv` as **Items**
4. `04_inventory_snapshot.csv` as **Inventory snapshot**
5. `05_sales_orders.csv` as **Orders**
6. `06_bank_statement.csv` as **Bank statement**

The party file creates exactly one company because order interpretation needs a
single delivering company. Orders and inventory then resolve existing records
by accounting code, SKU, and exact location name. The bank statement resolves
the customer and supplier by accounting code and creates unallocated incoming
and outgoing payments.

All CSV headers use canonical field names, so the deterministic suggestions are
complete. Change any selector on the mapping screen to test a one-off manual
mapping. `99_raw_payload.json` intentionally has no typed profile and demonstrates
lossless **Raw data only** storage.

Expected high-level result:

- 3 parties: company, customer, supplier
- 2 stock locations
- 3 items
- opening stock represented through adjustment movements
- 2 sales orders with 3 total lines and customer-delivery commitments
- 2 unallocated payments with balanced ledger postings

