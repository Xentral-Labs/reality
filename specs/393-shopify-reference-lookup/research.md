# Decisions

Reuse390 held-source basis and canonical company/location check, plus391 item
digest, rather than reconstructing authority from generic discovery labels.
Source-line SKU matching is an observation; selecting a record or stock unit does
not approve count meaning. A second bounded query detects role/activity/name/unit
and ambiguity changes before source is checked again. No network or long-lived
locks are involved. There is no schema and no compatibility overlay in this packet.

The result is a bounded optimistic read, not an absolute snapshot guarantee.
Native392 final-effect authorization revalidates and locks all current evidence;
this read does not substitute for that admission boundary.
