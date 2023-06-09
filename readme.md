# WowiPy
### WOWIPORT OPENWOWI API Python Wrapper
### Allgemein
WowiPy ermöglicht eine Abstrahierungsebene zur [OPENWOWI](https://docs.openwowi.de/grundlagen/eine-kurze-vorstellung-der-openwowi)-Api.
Dokumentation: https://github.com/seb-bau/WowiPy/wiki/WowiPy-Dokumentation

### Installation
````
pip install wowipy
````

### Funktionen aktuell
* Stammdatenabfrage (Personen, Unternehmen, Wirtschaftseinheiten, Gebäude, Nutzungseinheiten)
* Mietvertragabfrage (Nutzungsverträge, Vertragsnehmer)
* Caching (RAM und Disk)
* Verbindung ausgewählter Endpunkte (Beispiel: Es ist möglich, Vertragsnehmer direkt mit dem Nutzungsvertrag ausgeben
zu lassen)

### Geplante Funktionen
* Abbildung sämtlicher OPENWOWI-Endpunkte
* Suche inkl. Wildcards (in Ansätzen vorhanden)

### Anwendungsbeispiel
Abfrage des Start-Datums eines bestimmten Vertrages
````
from wowipy.wowipy import WowiPy

wowi = WowiPy(hostname="example.example.org", user="Example_User",
              password="Example_Password", api_key="Example_Key")

managements = wowi.get_license_agreements(license_agreement_idnum='00123.004.050.06')
print(managements[0].start_contract)
````
Ausgabe:
````
2009-02-05
````
