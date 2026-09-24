# Party email contract

Party create/update records accept `emails`, an optional array of at most 20 objects:

```json
{"email": "orders@example.com", "label": "Orders"}
```

Party discovery returns:

```json
{"emails": [{"email": "orders@example.com", "label": "Orders"}]}
```

For `family=party`, a query containing a syntactically valid email performs exact normalized email
matching in addition to existing name matching. Multiple Parties may be returned. No fuzzy or domain
match is performed.
