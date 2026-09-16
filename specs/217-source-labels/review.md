# Source terminology review

Source names the data-source context; Source Record names one received payload/record. SourceBadge and RuleEvidence navigate to source_record; external links target the source system. Provenance groups contain source-system and external-ID fields. Register Origin columns are data-source badges, not physical locations. The source-related English column, field and group keys become Source. Other English copy and technical identities remain unchanged.

Do not replace spatial origin, original movements, software source code, catalog source files, or every source-related explanatory sentence. Source code mappings remain specialized business mapping terminology. Original system names and external IDs stay verbatim.

Intentional localized UI examples:

| Key | Language | Before | After |
|---|---|---|---|
| Original source | de | Originalquelle | Ursprünglicher Source Record |
| Sources | de | Quellen | Sources |
| Source | de | Quelle | Source |
| Source systems | de | Quellsysteme | Source-Systeme |
| Source type | de | Quelltyp | Source-Typ |
| Source system | de | Quellsystem | Source-System |
| Source name | de | Quellenname | Source-Name |
| Source reference | de | Quellenbezug | Source-Referenz |
| Registered sources | de | Registrierte Quellen | Registrierte Sources |
| Open source | de | Quelle öffnen | Source Record öffnen |
| Select source system | de | Quellsystem auswählen | Source-System auswählen |
| Refine the search to find more source systems. | de | Suche eingrenzen, um weitere Quellsysteme zu finden. | Suche eingrenzen, um weitere Source-Systeme zu finden. |
| Source system not registered | de | Quellsystem nicht registriert | Source-System nicht registriert |
| Source system blocked | de | Quellsystem gesperrt | Source-System gesperrt |
| Show the original source | de | Originalquelle anzeigen | Source Record anzeigen |
| A newer source version exists | de | Es gibt eine neuere Quellversion | Eine neuere Version des Source Records ist vorhanden |
| Open in source system | de | Im Quellsystem öffnen | Im Source-System öffnen |
| Address of the source system | de | Adresse des Quellsystems | Adresse des Source-Systems |
| Address of the source system saved. | de | Adresse des Quellsystems gespeichert. | Adresse des Source-Systems gespeichert. |
| Only the beginning of the original source is shown. | de | Es wird nur der Anfang der Originalquelle angezeigt. | Es wird nur der Anfang des Source Records angezeigt. |
| Original source | nl | Oorspronkelijke bron | Oorspronkelijk Source Record |
| Sources | nl | Bronnen | Sources |
| Source | nl | Bron | Source |
| Source system | nl | Bron systeem | Source-systeem |
| Source systems | nl | Bron systemen | Source-systemen |
| Source type | nl | Type bron | Source-type |
| Source name | nl | Bronnaam | Source-naam |
| Source reference | nl | Bronverwijzing | Source-referentie |
| Registered sources | nl | Geregistreerde bronnen | Geregistreerde Sources |
| Open source | nl | Bron openen | Source Record openen |
| Select source system | nl | Bronsysteem selecteren | Source-systeem selecteren |
| Refine the search to find more source systems. | nl | Verfijn de zoekopdracht om meer bronsystemen te vinden. | Verfijn de zoekopdracht om meer Source-systemen te vinden. |
| Source system not registered | nl | Bronsysteem niet geregistreerd | Source-systeem niet geregistreerd |
| Source system blocked | nl | Bronsysteem geblokkeerd | Source-systeem geblokkeerd |
| Show the original source | nl | Oorspronkelijke bron tonen | Source Record bekijken |
| A newer source version exists | nl | Er bestaat een nieuwere bronversie | Er is een nieuwere versie van het Source Record |
| Open in source system | nl | Openen in bronsysteem | Openen in Source-systeem |
| Address of the source system | nl | Adres van het bronsysteem | Adres van het Source-systeem |
| Address of the source system saved. | nl | Adres van het bronsysteem opgeslagen. | Adres van het Source-systeem opgeslagen. |
| Only the beginning of the original source is shown. | nl | Alleen het begin van de oorspronkelijke bron wordt getoond. | Alleen het begin van het Source Record wordt getoond. |
| Original source | es | Fuente original | Source Record original |
| Sources | es | Fuentes | Sources |
| Source | es | Fuente | Source |
| Source system | es | Sistema de fuentes | Sistema Source |
| Source systems | es | Sistemas de fuentes | Sistemas Source |
| Source type | es | Tipo de fuente | Tipo de Source |
| Source name | es | Nombre del origen | Nombre de Source |
| Source reference | es | Referencia de origen | Referencia de Source |
| Registered sources | es | Fuentes registradas | Sources registradas |
| Open source | es | Abrir fuente | Abrir Source Record |
| Select source system | es | Seleccionar sistema de origen | Seleccionar sistema Source |
| Refine the search to find more source systems. | es | Refina la búsqueda para encontrar más sistemas de origen. | Refina la búsqueda para encontrar más sistemas Source. |
| Source system not registered | es | Sistema de origen no registrado | Sistema Source no registrado |
| Source system blocked | es | Sistema de origen bloqueado | Sistema Source bloqueado |
| Show the original source | es | Mostrar la fuente original | Ver Source Record |
| A newer source version exists | es | Existe una versión más reciente de la fuente | Existe una versión más reciente del Source Record |
| Open in source system | es | Abrir en el sistema de origen | Abrir en el sistema Source |
| Address of the source system | es | Dirección del sistema de origen | Dirección del sistema Source |
| Address of the source system saved. | es | Dirección del sistema de origen guardada. | Dirección del sistema Source guardada. |
| Only the beginning of the original source is shown. | es | Solo se muestra el principio de la fuente original. | Solo se muestra el principio del Source Record. |

Runtime review: mapping Provenance and Data source to the identical Source value confused reverse localization, causing the English UI to display Provenance. Their callers now use the Source key directly; their legacy translations remain unchanged. Original source retains an adjective around Source Record to avoid a second alias collision. The browser asserts the exact Source column caption in all four languages.
