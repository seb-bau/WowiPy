# WowiPy
### WOWIPORT OPENWOWI API Python Wrapper
### Allgemein
Achtung: Der angebotene Wrapper ist kein offizielles Produkt der Dr. Klein Wowi Digital!

Nutzen Sie OPENWOWI in Ihren Python-Projekten, ohne sich um die Syntax und Endpunkte kümmern zu müssen.  
WowiPy ist eine Sammlung aus Highlevel-Methoden, die u.A. die Stammdatenabfrage aus Wowiport vereinfacht.  
Darüber hinaus sollen im Laufe der Zeit weitere Funktionen eingebunden werden.

WowiPy befindet sich aktuell noch im Aufbau!

### Funktionen aktuell
* Stammdatenabfrage (Personen, Unternehmen, Wirtschaftseinheiten, Gebäude, Nutzungseinheiten)
* Mietvertragabfrage (Nutzungsverträge, Vertragsnehmer)

### Geplante Funktionen
* Abbildung sämtlicher OPENWOWI-Endpunkte
* Caching-Mechanismus (RAM und Disk)

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
