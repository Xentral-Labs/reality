# Language review

## Decisions
Review scope: quick-preview service labels, master-data fields/actions, and adjacent order, stock, shipment and finance controls. Catalog values were inspected after all overrides. Dutch/Spanish received a separate read-only review. This is an editorial review, not a claim of native-speaker sign-off.

Use ordinary ERP vocabulary and explicit action destinations. Keep existing correct payment terms, purchase units, conversion factors, lead times and debit/credit labels. Keep generic Fulfilled and Tracking: shared callers may include non-delivery fulfillment and lot/serial tracking. Keep canonical English model nouns and source content intact. A new Delivery progress heading avoids renaming Operational Reality in model-oriented views.

## Reviewed corrections
The following original/localized strings are intentional UI examples. Unlisted translations of a key remain unchanged.

| Key | Language | Before | After |
|---|---|---|---|
| Open full explanation | de | Vollständige Erklärung öffnen | Alle Details anzeigen |
| Open full explanation | nl | Volledige uitleg openen | Alle details bekijken |
| Open full explanation | es | Abrir explicación completa | Ver todos los detalles |
| More records are available in the full explanation. | de | Weitere Einträge findest du in der vollständigen Erklärung. | Weitere Einträge findest du unter „Alle Details anzeigen“. |
| More records are available in the full explanation. | nl | Meer gegevens staan in de volledige uitleg. | Bekijk alle details voor meer gegevens. |
| More records are available in the full explanation. | es | Hay más registros en la explicación completa. | Consulta todos los detalles para ver más registros. |
| Identity | de | Identität | Grunddaten |
| Identity | nl | Identiteit | Basisgegevens |
| Identity | es | Identidad | Datos generales |
| Inventory behaviour | de | Bestandsverhalten | Lager und Beschaffung |
| Inventory behaviour | nl | Voorraadgedrag | Voorraad en inkoop |
| Inventory behaviour | es | Comportamiento de inventario | Inventario y compras |
| Allows physical stock | de | Erlaubt physischen Bestand | Bestandsführung erlaubt |
| Allows physical stock | nl | Staat fysieke voorraad toe | Voorraad toegestaan |
| Allows physical stock | es | Permite stock físico | Permite almacenar existencias |
| Commercial defaults | de | Kaufmännische Vorgaben | Kaufmännische Einstellungen |
| Commercial defaults | nl | Commerciële standaardwaarden | Commerciële instellingen |
| Commercial defaults | es | Valores comerciales predeterminados | Condiciones comerciales |
| Business context | de | Geschäftlicher Zusammenhang | Zugehörige Geschäftsdaten |
| Business context | nl | Bedrijfscontext | Gerelateerde gegevens |
| Business context | es | Contexto comercial | Datos relacionados |
| Customer delivery holds | de | Kundensperren | Liefersperren für Kunden |
| Customer delivery holds | nl | Klantblokkades | Leveringsblokkades voor klanten |
| Customer delivery holds | es | Bloqueos del cliente | Bloqueos de entrega al cliente |
| Current tracking observations | de | Aktuelle Trackingmeldungen | Aktuelle Sendungsmeldungen |
| Current tracking observations | nl | Actuele trackingmeldingen | Actuele verzendmeldingen |
| Current tracking observations | es | Observaciones actuales de seguimiento | Últimas actualizaciones del envío |
| Warehouse and carrier observations differ | de | Lager- und Frachtführerbeobachtungen weichen voneinander ab | Angaben aus dem Lager und vom Transportdienstleister weichen voneinander ab |
| Warehouse and carrier observations differ | nl | Magazijn- en vervoerderswaarnemingen verschillen | De gegevens van het magazijn en de vervoerder komen niet overeen |
| Warehouse and carrier observations differ | es | Las observaciones del almacén y del transportista difieren | Los datos del almacén y del transportista no coinciden |
| Settled | nl | Afgehandeld | Vereffend |
| Settled | es | Resuelto | Liquidado |
| Allocated | nl | Toegekend | Toegewezen |
| Occurred | nl | Gebeurd | Tijdstip |
| Occurred | es | Ocurrió | Fecha y hora |
| Effective physical contents | es | Movimientos físicos registrados | Movimientos de mercancías registrados |
| Recorded | de | Erledigt | Erfasst |
| Physical | de | Physisch | Physischer Bestand |
| Physical | nl | Fysiek | Fysieke voorraad |
| Physical | es | Físico | Existencias físicas |
| Edit request | de | Auftrag bearbeiten | Änderung bearbeiten |
| Edit request | nl | Opdracht bewerken | Wijziging bewerken |
| Resume request | de | Auftrag fortsetzen | Änderung fortsetzen |
| Resume request | nl | Opdracht hervatten | Wijziging hervatten |
| A prepared request is saved. Check it before starting another change. | de | Ein vorbereiteter Auftrag ist gespeichert. Prüfe ihn, bevor du eine weitere Änderung startest. | Eine vorbereitete Änderung ist gespeichert. Prüfe sie, bevor du eine weitere Änderung beginnst. |
| A prepared request is saved. Check it before starting another change. | nl | Er is een voorbereide opdracht opgeslagen. Controleer deze voordat je een nieuwe wijziging start. | Er is een voorbereide wijziging opgeslagen. Controleer deze voordat je een nieuwe wijziging start. |
| Delivery progress (preview heading only) | de | Operative Reality | Lieferstatus |
| Delivery progress (preview heading only) | nl | Operationele Reality | Leveringsvoortgang |
| Delivery progress (preview heading only) | es | Operacional Reality | Estado de entrega |

| Check prepared request | de | Vorbereiteten Auftrag prüfen | Vorbereitete Änderung prüfen |
| Check prepared request | nl | Voorbereide opdracht controleren | Voorbereide wijziging controleren |

## Semantic review
Recorded means data was recorded, not completed. Settled retains financial settlement meaning and does not imply cash payment; credits/reductions can settle balances. Allocated agrees with the unallocated vocabulary. Delivery holds do not suspend every customer operation. Occurred is a date/time label. Item tracking remains generic; shipment updates have separate wording. Edit/resume request labels were traced to master-data change proposals, not sales orders. Physical denotes stock quantity, not an abstract adjective. No new units or inferred state.

## Analysis gate
Three requirements, four mapped tasks, 100% coverage, no unresolved ambiguities, no critical findings and no Constitution exceptions. Manual before/after review is the appropriate proof for low-risk copy; existing tests cover semantic and formatting boundaries.
