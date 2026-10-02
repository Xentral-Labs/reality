# Quickstart: Customer Item Numbers

1. On a customer, add "K-4711 Laufrad 28 Zoll" for our bike.
2. Enter an order for the customer with a line quoting K-4711. The line resolves to the bike and shows K-4711 with the customer's name.
3. Import an order file for the customer with K-4711 and an unknown K-9999.
   - The first line is promised.
   - The second is reported as an order line with an unknown item.
   - Assign it with "Für den Kunden merken"; the number is then listed on the customer.
4. Invoice the order: the invoice line shows K-4711.
