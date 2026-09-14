# Data model

No new table, column, identifier or stored projection. Stock is an observation over existing Movement and Reservation records. A Reservation's true operational parent is Commitment. Movement retains its existing commitment and correction relationships. OperationalException is derived on read, identified by the canonical class/subject identity, and can disappear after business records change. Source payloads and document status remain unchanged.
