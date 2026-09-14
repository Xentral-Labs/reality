# Installationsoptionen

Eine Reality-Installation hat zwei Verantwortlichkeiten:

```text
Menschen und Agenten
         |
         v
    Reality App
         |
         v
     PostgreSQL
```

Die **Reality App** liefert Produktoberfläche, Anwendungs-API, Geschäftsservices, Migrationen und
benötigte Hintergrundarbeit. **PostgreSQL** ist die einzige unterstützte Geschäftsdatenbank. Das
Docker-Paket verteilt diese Verantwortlichkeiten intern auf mehrere zusammenarbeitende Container.
Betreiber installieren und verwalten trotzdem eine Anwendung statt einer Sammlung öffentlicher
Websites.

Selbst gehostetes Reality ist das vollständige Produkt: dieselben Images wie in der Cloud,
MIT-lizenziert, ohne Funktionssperren und ohne Lizenzschlüssel. Wähle den Weg, der zu deiner
Situation passt.

| Option                              | Wähle sie, wenn                                                                                             | Du brauchst                                         |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| [Einzeiler-Setup](./installation)   | Reality soll in Minuten auf Laptop, VPS oder Heimserver laufen, mit Upgrade und Backup als je einem Befehl. | Docker mit Compose-v2-Plugin, curl                  |
| [Docker Compose](./docker-compose)  | Du willst jede Variable ausdrücklich setzen oder Reality in ein bestehendes Compose-Projekt aufnehmen.      | Docker Compose v2 und eine von Hand gefüllte `.env` |
| [Kubernetes mit Helm](./kubernetes) | Du betreibst bereits einen Cluster mit Ingress, Secret-Verwaltung und verwaltetem PostgreSQL.               | Helm 3, ein Kubernetes-Cluster, ein S3-Bucket       |
| [Railway](./railway)                | Du willst eine kurzlebige gehostete Demo ohne eigenen Server.                                               | Ein Railway-Konto und die Railway-CLI               |

Jede Option nutzt dieselben veröffentlichten Images aus `ghcr.io/xentral-labs`. Migrationen laufen,
bevor die App Verkehr annimmt, PostgreSQL ist nie öffentlich erreichbar, und der Schlüssel für
gespeicherte Zugangsdaten liegt in deiner Konfiguration, nie in der Datenbank.

Die öffentliche Reality-Website und diese Dokumentation betreibt der Produktanbieter. Sie gehören
nicht zu einer Kundeninstallation. Eine später angebotene verwaltete Infrastruktur erhält einen
eigenen Contract, sobald sie verfügbar ist.

Nach der Installation erklärt [Mit Docker betreiben](./deployment) Upgrades, Backups, Health und die
Sicherheitscheckliste. Laufzeitwerte stehen in der [Umgebungsreferenz](/de/reference/environment).
