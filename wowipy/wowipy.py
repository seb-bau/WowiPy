import copy
import logging
import humps
import pickle
from jsonmerge import Merger
from wowipy.rest_adapter import RestAdapter
from wowipy.exceptions import WowiPyException
from wowipy.models import *


class WowiPy:
    CACHE_LICENSE_AGREEMENTS = "license_agreements"
    CACHE_CONTRACTORS = "contractors"
    CACHE_PERSONS = "persons"
    CACHE_ECONOMIC_UNITS = "license_agreements"
    CACHE_BUILDING_LANDS = "building_lands"
    CACHE_USE_UNITS = "use_units"

    SEARCH_POS_LEFT = "begins"
    SEARCH_POS_CONTAINS = "contains"

    def __init__(self, hostname: str, user: str, password: str, api_key: str, version: str = 'v1.2',
                 logger: logging.Logger = None):
        self._rest_adapter = RestAdapter(hostname, user, password, api_key, version, logger)
        self._cache = {
            self.CACHE_LICENSE_AGREEMENTS: [],
            self.CACHE_CONTRACTORS: [],
            self.CACHE_PERSONS: [],
            self.CACHE_USE_UNITS: [],
            self.CACHE_BUILDING_LANDS: [],
            self.CACHE_ECONOMIC_UNITS: []
        }

    def cache_to_disk(self, cache_type: str, file_name: str):
        if cache_type not in self._cache.keys():
            raise WowiPyException("Unknown Cache Type")

        with open(file_name, 'wb') as fp:
            pickle.dump(self._cache.get(cache_type), fp)

    def cache_from_disk(self, cache_type: str, file_name: str):
        if cache_type not in self._cache.keys():
            raise WowiPyException("Unknown Cache Type")

        with open(file_name, 'rb') as fp:
            self._cache[cache_type] = pickle.load(fp)

    def search_string(self, haystack: str, needle: str, search_mode: str = SEARCH_POS_CONTAINS) -> bool:
        haystack = haystack.lower()
        needle = needle.lower()
        if (search_mode == self.SEARCH_POS_CONTAINS and needle in haystack) or \
                (search_mode == self.SEARCH_POS_LEFT and haystack.startswith(needle)):
            return True
        else:
            return False

    def check_person_match(self, person_obj: Person,
                           search_name: str = None,
                           search_address: str = None,
                           search_phone: str = None,
                           search_email: str = None,
                           search_mode: str = SEARCH_POS_CONTAINS) -> bool:
        if person_obj is None:
            return False

        if search_name is not None:
            if person_obj.natural_person is not None:
                if person_obj.natural_person.last_name is not None:
                    if person_obj.natural_person.first_name is not None:
                        first_name = person_obj.natural_person.first_name.lower()
                    else:
                        first_name = ""
                    last_name = person_obj.natural_person.last_name.lower()
                    if self.search_string(first_name, search_name, search_mode) or \
                            self.search_string(last_name, search_name, search_mode) or \
                            self.search_string(f"{first_name} {last_name}", search_name, search_mode) or \
                            self.search_string(f"{last_name}, {first_name}", search_name, search_mode):
                        return True
            if person_obj.legal_person is not None:
                if person_obj.legal_person.long_name1 is not None:
                    if self.search_string(person_obj.legal_person.long_name1, search_name, search_mode):
                        return True

        if search_address is not None:
            address: Address
            address_found = False
            if person_obj.addresses is not None:
                for address in person_obj.addresses:
                    street = address.street_complete
                    if self.search_string(street, search_address, search_mode):
                        address_found = True
                        break
            if address_found:
                return True

        if search_phone is not None:
            communication: Communication
            phone_found = False
            if person_obj.communications is None:
                return False
            for comm in person_obj.communications:
                if comm.communication_type.name == "Festnetz" or comm.communication_type.name == "Handynummer":
                    content = comm.content.strip()
                    search_phone = search_phone.strip()
                    # Problem: Es gibt diverse gängige Formate für Rufnummern. Es gibt keine Formatvorgabe in
                    # Wowiport, also können wir auch nicht vorhersehen, welches gewählt wurde.
                    # Wenn ein + gefunden wurde, werden die ersten drei Zeichen von needle und haystack entfernt.
                    # Ansonsten werden alle führenden Nullen entfernt
                    if content.startswith('+'):
                        content = content[3:]
                    if search_phone.startswith('+'):
                        search_phone = search_phone[3:]
                    if search_phone.startswith('0049'):
                        search_phone = search_phone[4:]
                    if content.startswith('0049'):
                        content = content[4:]

                    content = content.lstrip('0')
                    search_phone = search_phone.lstrip('0')

                    content = content.replace(' ', '')
                    search_phone = search_phone.replace(' ', '')

                    if self.search_string(content, search_phone, search_mode):
                        phone_found = True
                        break
            if phone_found:
                return True

        if search_email is not None:
            communication: Communication
            email_found = False
            if person_obj.communications is None:
                return False
            for comm in person_obj.communications:
                if comm.communication_type.name == "E-Mail":
                    content = comm.content.strip()
                    if self.search_string(content, search_email, search_mode):
                        email_found = True
                        break
            if email_found:
                return True

        return False

    def search_contractor(self, search_name: str = None, search_address: str = None, search_phone: str = None,
                          search_email: str = None, max_results: int = 10,
                          search_mode: str = SEARCH_POS_CONTAINS, allow_duplicates: bool = False) -> List:
        person_ids = []
        res = []
        entry: Contractor
        for entry in self._cache.get(self.CACHE_CONTRACTORS):
            if len(res) >= max_results:
                break

            if entry.person.id_ in person_ids and not allow_duplicates:
                continue

            if self.check_person_match(person_obj=entry.person,
                                       search_name=search_name,
                                       search_address=search_address,
                                       search_phone=search_phone,
                                       search_email=search_email,
                                       search_mode=search_mode):
                res.append(entry)
                person_ids.append(entry.person.id_)

        return res

    def search_person(self, search_name: str = None, search_address: str = None, search_phone: str = None,
                      search_email: str = None, max_results: int = 10,
                      search_mode: str = SEARCH_POS_CONTAINS) -> List:
        res = []
        entry: Person
        for entry in self._cache.get(self.CACHE_PERSONS):
            if len(res) >= max_results:
                break

            if self.check_person_match(person_obj=entry,
                                       search_name=search_name,
                                       search_address=search_address,
                                       search_phone=search_phone,
                                       search_email=search_email,
                                       search_mode=search_mode):
                res.append(entry)

        return res

    def search_cache(self, search_str: str, cache_types: Dict = None, max_results: int = 10,
                     find_pos: str = SEARCH_POS_CONTAINS) -> Dict:
        if cache_types is None:
            scope = self._cache
        else:
            scope = {}
            for ttype in self._cache.keys():
                scope[ttype] = self._cache.get(ttype)

        res = {}
        res_count = 0
        for tkey in scope.keys():
            if res_count >= max_results:
                break
            res[tkey] = []
            for entry in self._cache.get(tkey):
                if res_count >= max_results:
                    break
                if tkey == self.CACHE_LICENSE_AGREEMENTS:
                    sobj = entry
                    haystack = {
                        sobj.id_num
                    }
                    if (find_pos == self.SEARCH_POS_CONTAINS and search_str in sobj.id_num) or \
                            (find_pos == self.SEARCH_POS_LEFT and sobj.id_num.startswith(search_str)):
                        if res.get(tkey) is None:
                            res[tkey] = copy.deepcopy(sobj)
                        else:
                            res[tkey].append(copy.deepcopy(sobj))
                        res_count += 1

        return res

    def search_building(self, search_address: str = None,
                        filter_idnum_above: int = 0,
                        max_results: int = 10,
                        search_mode: str = SEARCH_POS_CONTAINS) -> List:
        res = []
        entry: BuildingLand
        search_address = search_address.replace(" ", "").strip()
        for entry in self._cache.get(self.CACHE_BUILDING_LANDS):
            if filter_idnum_above > 0:
                entry_idnum = entry.id_num
                if entry_idnum is not None:
                    entry_idnum_parts = entry_idnum.split(".")
                    building_idnum = entry_idnum_parts[-1]
                    try:
                        building_idnum_int = int(building_idnum)
                        if building_idnum_int > filter_idnum_above:
                            continue
                    except ValueError:
                        pass

            if len(res) >= max_results:
                break

            if search_address is not None:
                address: Address
                if entry.estate_address is not None:
                    street = entry.estate_address.street_complete.replace(" ", "").strip()
                    if self.search_string(street, search_address, search_mode):
                        res.append(entry)
                        continue
                    elif self.search_string(street, search_address.replace("str.", "straße").replace("Str.", "Straße"),
                                            search_mode):
                        res.append(entry)
                        continue
        return res

    def build_license_agreement_cache(self,
                                      economic_unit_idnum: str = None,
                                      use_unit_idnum: str = None,
                                      license_agreement_active_on: datetime = None,
                                      add_args: Dict = None) -> None:
        """
        Erstellt einen temporären Cache, der alle Ergebnisse fassen kann
        :param economic_unit_idnum: (Optional) Nur Verträge dieser Wirtschaftseinheit zurückgeben
        :type economic_unit_idnum: str
        :param use_unit_idnum: (Optional) Nur Verträge dieser Nutzungseinheit zurückgeben
        :type use_unit_idnum: str
        :param license_agreement_active_on: (Optional) Nur Verträge, die zu diesem Zeitpunkt aktiv sind
        :type license_agreement_active_on: datetime
        :param add_args: Zusätzliche Parameter die per GET an die URL angehängt werden
        :type add_args: Dict
        :return: Liste mit Nutzungsverträgen (auch bei nur einem Ergebnis!)
        :rtype: Liste[LicenseAgreement]
        """
        limit = 100
        offset = 0
        ret_list = self.get_license_agreements(economic_unit_idnum=economic_unit_idnum,
                                               use_unit_idnum=use_unit_idnum,
                                               license_agreement_active_on=license_agreement_active_on,
                                               add_args=add_args, limit=limit, offset=offset)
        response_len = len(ret_list)

        while response_len == limit:
            offset += limit
            t_resp = self.get_license_agreements(economic_unit_idnum=economic_unit_idnum,
                                                 use_unit_idnum=use_unit_idnum,
                                                 license_agreement_active_on=license_agreement_active_on,
                                                 add_args=add_args, limit=limit, offset=offset)
            response_len = len(t_resp)
            ret_list = ret_list + t_resp
            print(f"License Agreements {len(ret_list)}")

        self._cache[self.CACHE_LICENSE_AGREEMENTS] = ret_list

    def build_economic_unit_cache(self,
                                  management_idnum: str = None,
                                  owner_number: str = None,
                                  add_args: Dict = None) -> None:
        """
        Erstellt einen temporären Cache, der alle Ergebnisse fassen kann
        :param management_idnum:
        :type management_idnum:
        :param owner_number:
        :type owner_number:
        :param add_args: Zusätzliche Parameter die per GET an die URL angehängt werden
        :type add_args: Dict
        :return: Liste mit Nutzungsverträgen (auch bei nur einem Ergebnis!)
        :rtype: Liste[LicenseAgreement]
        """
        limit = 100
        offset = 0
        ret_list = self.get_economic_units(management_idnum=management_idnum,
                                           owner_number=owner_number,
                                           add_args=add_args, limit=limit, offset=offset)
        response_len = len(ret_list)

        while response_len == limit:
            offset += limit
            t_resp = self.get_economic_units(management_idnum=management_idnum,
                                             owner_number=owner_number,
                                             add_args=add_args, limit=limit, offset=offset)
            response_len = len(t_resp)
            ret_list = ret_list + t_resp
            print(f"Economic Units {len(ret_list)}")

        self._cache[self.CACHE_ECONOMIC_UNITS] = ret_list

    def build_building_land_cache(self,
                                  management_idnum: str = None,
                                  owner_number: str = None,
                                  economic_idnum: str = None,
                                  add_args: Dict = None) -> None:
        """
        Erstellt einen temporären Cache, der alle Ergebnisse fassen kann

        :param management_idnum:
        :type management_idnum:
        :param owner_number:
        :type owner_number:
        :param economic_idnum:
        :type economic_idnum:
        :param add_args: Zusätzliche Parameter die per GET an die URL angehängt werden
        :type add_args: Dict
        :return: Liste mit Nutzungsverträgen (auch bei nur einem Ergebnis!)
        :rtype: Liste[LicenseAgreement]
        """
        limit = 100
        offset = 0
        ret_list = self.get_building_lands(management_idnum=management_idnum,
                                           owner_number=owner_number,
                                           economic_unit_idnum=economic_idnum,
                                           add_args=add_args, limit=limit, offset=offset)
        response_len = len(ret_list)

        while response_len == limit:
            offset += limit
            t_resp = self.get_building_lands(management_idnum=management_idnum,
                                             owner_number=owner_number,
                                             economic_unit_idnum=economic_idnum,
                                             add_args=add_args, limit=limit, offset=offset)
            response_len = len(t_resp)
            ret_list = ret_list + t_resp
            print(f"Building lands {len(ret_list)}")

        self._cache[self.CACHE_BUILDING_LANDS] = ret_list

    def build_use_unit_cache(self,
                             building_land_idnum: str = None,
                             economic_unit_idnum: str = None,
                             management_idnum: str = None,
                             owner_number: str = None,
                             add_args: Dict = None) -> None:
        """
        Erstellt einen temporären Cache, der alle Ergebnisse fassen kann

        :param economic_unit_idnum:
        :type economic_unit_idnum:
        :param building_land_idnum:
        :type building_land_idnum:
        :param management_idnum:
        :type management_idnum:
        :param owner_number:
        :type owner_number:
        :param add_args: Zusätzliche Parameter die per GET an die URL angehängt werden
        :type add_args: Dict
        :return: Liste mit Nutzungsverträgen (auch bei nur einem Ergebnis!)
        :rtype: Liste[LicenseAgreement]
        """
        limit = 100
        offset = 0
        ret_list = self.get_use_units(management_idnum=management_idnum,
                                      building_land_idnum=building_land_idnum,
                                      owner_number=owner_number,
                                      economic_unit_idnum=economic_unit_idnum,
                                      add_args=add_args, limit=limit, offset=offset)
        response_len = len(ret_list)

        while response_len == limit:
            offset += limit
            t_resp = self.get_use_units(management_idnum=management_idnum,
                                        building_land_idnum=building_land_idnum,
                                        owner_number=owner_number,
                                        economic_unit_idnum=economic_unit_idnum,
                                        add_args=add_args, limit=limit, offset=offset)
            response_len = len(t_resp)
            ret_list = ret_list + t_resp
            print(f"Use units {len(ret_list)}")

        self._cache[self.CACHE_USE_UNITS] = ret_list

    def build_contractor_cache(self,
                               license_agreement_id: int = None,
                               person_id: int = None,
                               license_agreement_active_on: datetime = None,
                               contractual_use_active_on: datetime = None,
                               add_args: Dict = None) -> None:
        """
        Erstellt einen temporären Cache, der alle Ergebnisse fassen kann
        :param contractual_use_active_on:
        :type contractual_use_active_on:
        :param person_id:
        :type person_id:
        :param license_agreement_id:
        :type license_agreement_id:
        :param license_agreement_active_on: (Optional) Nur Verträge, die zu diesem Zeitpunkt aktiv sind
        :type license_agreement_active_on: datetime
        :param add_args: Zusätzliche Parameter die per GET an die URL angehängt werden
        :type add_args: Dict
        :return: Liste mit Nutzungsverträgen (auch bei nur einem Ergebnis!)
        :rtype: Liste[LicenseAgreement]
        """
        limit = 100
        offset = 0
        ret_list = self.get_contractors(license_agreement_id=license_agreement_id,
                                        person_id=person_id,
                                        contractual_use_active_on=contractual_use_active_on,
                                        license_agreement_active_on=license_agreement_active_on,
                                        add_args=add_args, limit=limit, offset=offset)
        response_len = len(ret_list)

        while response_len == limit:
            offset += limit
            t_resp = self.get_contractors(license_agreement_id=license_agreement_id,
                                          person_id=person_id,
                                          contractual_use_active_on=contractual_use_active_on,
                                          license_agreement_active_on=license_agreement_active_on,
                                          add_args=add_args, limit=limit, offset=offset)
            response_len = len(t_resp)
            ret_list = ret_list + t_resp
            print(f"Contractors {len(ret_list)}")

        self._cache[self.CACHE_CONTRACTORS] = ret_list

    def build_person_cache(self,
                           person_id: int = None,
                           add_args: Dict = None) -> None:

        limit = 100
        offset = 0
        ret_list = self.get_persons(person_id=person_id,
                                    add_args=add_args, limit=limit, offset=offset)
        response_len = len(ret_list)

        while response_len == limit:
            offset += limit
            t_resp = self.get_persons(person_id=person_id,
                                      add_args=add_args, limit=limit, offset=offset)
            response_len = len(t_resp)
            ret_list = ret_list + t_resp
            print(f"Persons {len(ret_list)}")

        self._cache[self.CACHE_PERSONS] = ret_list

    def get_license_agreements(self,
                               economic_unit_idnum: str = None,
                               use_unit_idnum: str = None,
                               license_agreement_idnum: str = None,
                               license_agreement_active_on: datetime = None,
                               person_idnum: str = None,
                               limit: int = None,
                               offset: int = 0,
                               add_args: Dict = None,
                               add_contractors: bool = False,
                               use_cache: bool = False,
                               ) -> List[LicenseAgreement]:
        """
        Gibt eine Liste mit Nutzungsverträgen zurück
        :param add_contractors:
        :type add_contractors:
        :param use_cache:
        :type use_cache:
        :param offset: Verschiebung der Abfrage. Default: 0
        :type offset: int
        :param economic_unit_idnum: (Optional) Nur Verträge dieser Wirtschaftseinheit zurückgeben
        :type economic_unit_idnum: str
        :param use_unit_idnum: (Optional) Nur Verträge dieser Nutzungseinheit zurückgeben
        :type use_unit_idnum: str
        :param license_agreement_idnum: (Optional) Nur diesen Vertrag zurückgeben
        :type license_agreement_idnum: str
        :param license_agreement_active_on: (Optional) Nur Verträge, die zu diesem Zeitpunkt aktiv sind
        :type license_agreement_active_on: datetime
        :param person_idnum: (Optional) NUr Verträge dieser Person zurückgeben
        :type person_idnum: str
        :param limit: Maximale Anzahl an zurückgegebenen Einträgen (max = default = 100)
        :type limit: int
        :param add_args: Zusätzliche Parameter die per GET an die URL angehängt werden
        :type add_args: Dict
        :return: Liste mit Nutzungsverträgen (auch bei nur einem Ergebnis!)
        :rtype: Liste[LicenseAgreement]
        """
        filter_params = {}
        if economic_unit_idnum is not None:
            filter_params['EconomicUnitIdNum'] = economic_unit_idnum
        if use_unit_idnum is not None:
            filter_params['UseUnitNumber'] = use_unit_idnum
        if license_agreement_idnum is not None:
            filter_params['LicenseAgreementIdNum'] = license_agreement_idnum
        if license_agreement_active_on is not None:
            filter_params['licenseAgreementActiveOn'] = license_agreement_active_on.strftime("%Y-%m-%d")
        if person_idnum is not None:
            filter_params['personIdNum'] = person_idnum
        if limit is not None:
            filter_params['limit'] = limit
        filter_params['offset'] = offset
        if add_args is not None:
            filter_params.update(add_args)

        retlist = []
        if use_cache:
            cache_entry: LicenseAgreement
            for cache_entry in self._cache[self.CACHE_LICENSE_AGREEMENTS]:
                if (economic_unit_idnum is not None and cache_entry.use_unit.economic_unit == economic_unit_idnum) or \
                        (use_unit_idnum is not None and cache_entry.use_unit.use_unit_number == use_unit_idnum) or \
                        (license_agreement_idnum is not None and cache_entry.id_num == license_agreement_idnum):
                    if add_contractors:
                        print(cache_entry.id_)
                        cache_entry.contractors = self.get_contractors(license_agreement_id=cache_entry.id_,
                                                                       use_cache=True)
                    retlist.append(copy.deepcopy(cache_entry))
        else:
            result = self._rest_adapter.get(endpoint='RentAccounting/LicenseAgreements', ep_params=filter_params)

            for entry in result.data:
                data = dict(humps.decamelize(entry))
                data['id_'] = data.pop('id')
                if add_contractors:
                    data['contractors'] = self.get_contractors(license_agreement_id=data.get("id_"))
                ret_la = LicenseAgreement(**data)
                retlist.append(ret_la)
        return retlist

    def get_managements(self,
                        management_idnum: str = None,
                        limit: int = None,
                        offset: int = 0,
                        add_args: Dict = None) -> List[Management]:
        """
        Gibt eine Liste mit Managements zurück
        :param offset: Verschiebung der Abfrage. Default: 0
        :type offset: int
        :param management_idnum: (Optional) Nur das Management mit dieser IdNum zurückgeben
        :type management_idnum: str
        :param limit: Maximale Anzahl an Einträgen (max = default = 100)
        :type limit: int
        :param add_args: Zusätzliche Parameter, die per GET an die URL angehängt werden
        :type add_args: Dict
        :return: Liste mit Managements (auch bei nur einem Ergebnis!)
        :rtype: List[Management]
        """
        filter_params = {}
        if management_idnum is not None:
            filter_params['managementIdNum'] = management_idnum
        if limit is not None:
            filter_params['limit'] = limit
        filter_params['offset'] = offset

        # Ein paar Standardwerte, können aber durch add_args überschrieben werden
        filter_params['includeMainAddress'] = 'true'
        filter_params['includeMainCommunication'] = 'true'
        filter_params['includeMainBankaccount'] = 'true'
        filter_params['includePersonAddresses'] = 'true'
        filter_params['includePersonCommunications'] = 'true'
        filter_params['includePersonBankAccounts'] = 'true'
        filter_params['includeCompanyCodes'] = 'true'

        if add_args is not None:
            filter_params.update(add_args)

        result = self._rest_adapter.get(endpoint='CommercialInventory/Managements', ep_params=filter_params)
        retlist = []
        for entry in result.data:
            data = dict(humps.decamelize(entry))
            data['id_'] = data.pop('id')
            ret_la = Management(**data)
            retlist.append(ret_la)
        return retlist

    def get_economic_units(self,
                           management_idnum: str = None,
                           owner_number: str = None,
                           economic_idnum: str = None,
                           limit: int = None,
                           offset: int = 0,
                           add_args: Dict = None) -> List[EconomicUnit]:
        """
        Gitb eine Liste mit Wirtschaftseinheiten zurück
        :param offset: Verschiebung der Abfrage. Default: 0
        :type offset: int
        :param management_idnum: (Optional) Nur Wirtschaftseinheiten dieses Managements zurückgeben
        :type management_idnum: str
        :param owner_number: (Optional) Nur Wirtschaftseinheiten dieses Besitzers zurückgeben
        :type owner_number: str
        :param economic_idnum: (Optional) Nur die Wirtschaftseinheit mit dieser Nummer zurückgeben
        :type economic_idnum: str
        :param limit: Maximale Anzahl an zurückgegebenen Einträgen (max = default = 100)
        :type limit: int
        :param add_args: Zusätzliche Parameter, die per GET an die URL angehängt werden
        :type add_args: Dict
        :return: Liste mit Wirtschaftseinheiten (auch bei nur einem Ergebnis!)
        :rtype: List[EconomicUnit]
        """
        filter_params = {}
        if management_idnum is not None:
            filter_params['managementIdNum'] = management_idnum
        if owner_number is not None:
            filter_params['ownerNumber'] = owner_number
        if economic_idnum is not None:
            filter_params['economicIdNum'] = economic_idnum
        if limit is not None:
            filter_params['limit'] = limit
        filter_params['offset'] = offset

        # Ein paar Standardwerte, können aber durch add_args überschrieben werden
        filter_params['includeCompanyCode'] = 'true'

        if add_args is not None:
            filter_params.update(add_args)

        result = self._rest_adapter.get(endpoint='CommercialInventory/EconomicUnits', ep_params=filter_params)
        retlist = []
        for entry in result.data:
            data = dict(humps.decamelize(entry))
            data['id_'] = data.pop('id')
            ret_la = EconomicUnit(**data)
            retlist.append(ret_la)
        return retlist

    def get_building_lands(self,
                           management_idnum: str = None,
                           owner_number: str = None,
                           economic_unit_idnum: str = None,
                           building_land_idnum: str = None,
                           limit: int = None,
                           offset: int = 0,
                           add_args: Dict = None,
                           fetch_all: bool = False,
                           use_cache: bool = False) -> List[BuildingLand]:
        """
        Gibt ein oder mehrere Gebäude als Liste zurück.
        :param fetch_all:
        :type fetch_all:
        :param use_cache:
        :type use_cache:
        :param offset: Verschiebung der Abfrage. Default: 0
        :type offset: int
        :param management_idnum: (Optional) Nur Gebäude dieses Managements zurückgeben
        :type management_idnum: str
        :param owner_number: (Optional) Nur Gebäude dieses Eigentümers zurückgeben
        :type owner_number: str
        :param economic_unit_idnum: (Optional) Nur Gebäude dieser Wirtschaftseinheit zurückgeben
        :type economic_unit_idnum: str
        :param building_land_idnum: (Optional) Nur das Gebäude mit dieser IdNum zurückgeben
        :type building_land_idnum: str
        :param limit: Maxmiale Anzahl an Einträgen, die zurückgegeben werden sollen (max = default = 100)
        :type limit: 100
        :param add_args: Zusätzlich GET-Parameter als DICT, die an die URL angehängt werden.
        :type add_args: Dict
        :return: Liste mit Gebäuden (auch bei nur einem Ergebnis!)
        :rtype: List[BuildingLand]
        """

        filter_params = {}
        if management_idnum is not None:
            filter_params['managementIdNum'] = management_idnum
        if owner_number is not None:
            filter_params['ownerNumber'] = owner_number
        if economic_unit_idnum is not None:
            filter_params['economicIdNum'] = economic_unit_idnum
        if building_land_idnum is not None:
            filter_params['buildingLandIdNum'] = building_land_idnum
        if limit is not None:
            filter_params['limit'] = limit
        filter_params['offset'] = offset

        # Ein paar Standardwerte, können aber durch add_args überschrieben werden
        filter_params['includeCompanyCode'] = 'true'
        filter_params['showNullValues'] = 'true'

        if add_args is not None:
            filter_params.update(add_args)
        retlist = []
        if use_cache:
            cache_entry: BuildingLand
            for cache_entry in self._cache[self.CACHE_BUILDING_LANDS]:
                if (economic_unit_idnum is not None and
                    cache_entry.economic_unit.id_num == economic_unit_idnum) or \
                        economic_unit_idnum is None:
                    retlist.append(copy.deepcopy(cache_entry))
        else:
            if not fetch_all:
                result = self._rest_adapter.get(endpoint='CommercialInventory/BuildingLands', ep_params=filter_params)
            else:
                result = Result(0, "", [])
                merge_schema = {"mergeStrategy": "append"}
                merger = Merger(schema=merge_schema)
                filter_params['offset'] = 0
                filter_params['limit'] = 100
                response_count = 100
                while response_count == 100:
                    part_result = self._rest_adapter.get(endpoint='CommercialInventory/BuildingLands',
                                                         ep_params=filter_params)
                    result.data = merger.merge(result.data, part_result.data)
                    filter_params['offset'] += 100
                    response_count = len(part_result.data)
                    print(f"Building-Count: {len(result.data)}")

            for entry in result.data:
                data = dict(humps.decamelize(entry))
                data['id_'] = data.pop('id')
                data.get('estate_address')['zip_'] = data.get('estate_address').pop('zip')
                ret_la = BuildingLand(**data)
                retlist.append(ret_la)
        return retlist

    def get_owners(self,
                   owner_number: str = None,
                   limit: int = None,
                   offset: int = 0,
                   add_args: Dict = None) -> List[Owner]:
        """
        :param offset: Verschiebung der Abfrage. Default: 0
        :type offset: int
        :param owner_number: (Optional) Nur Owner mit der entsprechenden IdNum
        :type owner_number: str
        :param limit: (Optional) Anzahl der Rückgabewerte (maximal = default = 100)
        :type limit: int
        :param add_args: (Optional) Zusätzliche GET-Parameter als Dict
        :type add_args: Dict
        :return: Owner als Liste (auch bei nur einem Ergebnis!)
        :rtype: List[Owner]
        """
        filter_params = {}
        if owner_number is not None:
            filter_params['ownerNumber'] = owner_number
        if limit is not None:
            filter_params['limit'] = limit
        filter_params['offset'] = offset

        # Ein paar Standardwerte, können aber durch add_args überschrieben werden
        filter_params['includeMainAddress'] = 'true'
        filter_params['includeMainCommunication'] = 'true'
        filter_params['includeMainBankaccount'] = 'true'
        filter_params['includePersonAddresses'] = 'true'
        filter_params['includePersonCommunications'] = 'true'
        filter_params['includePersonBankAccounts'] = 'true'
        filter_params['includeCompanyCodes'] = 'true'

        if add_args is not None:
            filter_params.update(add_args)

        result = self._rest_adapter.get(endpoint='CommercialInventory/Owners', ep_params=filter_params)
        retlist = []
        for entry in result.data:
            data = dict(humps.decamelize(entry))
            data['id_'] = data.pop('id')
            if data.get('estate_address') is not None:
                data.get('estate_address')['zip_'] = data.get('estate_address').pop('zip')
            ret_la = Owner(**data)
            retlist.append(ret_la)
        return retlist

    def get_commissioning_invoice_receipts(self,
                                           limit: int = None,
                                           offset: int = 0,
                                           add_args: Dict = None,
                                           fetch_all: bool = False) -> List[InvoiceReceipt]:
        filter_params = {}
        if limit is not None:
            filter_params['limit'] = limit
        filter_params['offset'] = offset

        # Ein paar Standardwerte, können aber durch add_args überschrieben werden
        filter_params['showNullValues'] = 'true'
        filter_params['includePaymentOrder'] = 'true'

        if add_args is not None:
            filter_params.update(add_args)
        retlist = []

        if not fetch_all:
            result = self._rest_adapter.get(endpoint='CommissioningRead/InvoiceReceipt/CommissionItems',
                                            ep_params=filter_params)
        else:
            result = Result(0, "", [])
            merge_schema = {"mergeStrategy": "append"}
            merger = Merger(schema=merge_schema)
            filter_params['offset'] = 0
            filter_params['limit'] = 100
            response_count = 100
            while response_count == 100:
                part_result = self._rest_adapter.get(endpoint='CommissioningRead/InvoiceReceipt/CommissionItems',
                                                     ep_params=filter_params)
                result.data = merger.merge(result.data, part_result.data)
                filter_params['offset'] += 100
                response_count = len(part_result.data)
                print(f"Receipt-Count: {len(result.data)}")

        for entry in result.data:
            data = dict(humps.decamelize(entry))
            data['id_'] = data.pop('id')
            ret_la = InvoiceReceipt(**data)
            retlist.append(ret_la)

        return retlist

    def get_use_units(self,
                      use_unit_idnum: str = None,
                      building_land_idnum: str = None,
                      economic_unit_idnum: str = None,
                      management_idnum: str = None,
                      owner_number: str = None,
                      limit: int = None,
                      offset: int = 0,
                      add_args: Dict = None,
                      use_cache: bool = False) -> List[UseUnit]:
        """
        Gibt eine Liste von Nutzungseinheiten zurück
        :param use_cache:
        :type use_cache:
        :param use_unit_idnum: (Optional) Nur diese Nutzungseinheit zurückgeben
        :type use_unit_idnum: str
        :param building_land_idnum: (Optional) Nur Einheiten dieses Gebäudes zurückgeben
        :type building_land_idnum: str
        :param economic_unit_idnum: (Optional) Nur Einheiten dieser Wirtschaftseinheit zurückgeben
        :type economic_unit_idnum: str
        :param management_idnum: (Optional) Nur Einheiten dieses Managements zurückgeben
        :type management_idnum: str
        :param owner_number: (Optional) Nur Einheiten dieses Besitzers zurückgeben
        :type owner_number: str
        :param limit: Maximale Anzahl an Einträgen, die zurückgegeben werden (max = default = 100)
        :type limit: int
        :param offset: (Optional) Verschiebung der Abfrage. Default: 0
        :type offset: int
        :param add_args: Zusätzliche Parameter, die per GET an die URL angehängt werden
        :type add_args: Dict
        :return: Liste aus Nutzungseinheiten (auch bei nur einem Ergebnis!)
        :rtype: List[UseUnit]
        """
        filter_params = {}
        if use_unit_idnum is not None:
            filter_params['useUnitNumber'] = use_unit_idnum
        if building_land_idnum is not None:
            filter_params['buildingLandIdNum'] = building_land_idnum
        if economic_unit_idnum is not None:
            filter_params['EconomicUnitIdNum'] = economic_unit_idnum
        if management_idnum is not None:
            filter_params['managementIdNum'] = management_idnum
        if owner_number is not None:
            filter_params['ownerNumber'] = owner_number
        if limit is not None:
            filter_params['limit'] = limit
        filter_params['offset'] = offset

        # Standardparameter, können via add_args überschrieben werden
        filter_params['includeUseUnitTypes'] = 'true'
        filter_params['includeBillingUnits'] = 'true'
        filter_params['includeMarketingTags'] = 'false'
        filter_params['showNullValues'] = 'true'

        if add_args is not None:
            filter_params.update(add_args)
        retlist = []

        if use_cache:
            cache_entry: UseUnit
            for cache_entry in self._cache[self.CACHE_USE_UNITS]:
                if (use_unit_idnum is not None and cache_entry.id_num == use_unit_idnum) or \
                        (building_land_idnum is not None and
                         cache_entry.building_land.id_num == building_land_idnum) or \
                        (economic_unit_idnum is not None and
                         cache_entry.economic_unit.id_num == economic_unit_idnum):
                    retlist.append(copy.deepcopy(cache_entry))
        else:
            result = self._rest_adapter.get(endpoint='CommercialInventory/UseUnits', ep_params=filter_params)
            for entry in result.data:
                data = dict(humps.decamelize(entry))
                data['id_'] = data.pop('id')
                if data.get('estate_address') is not None:
                    data.get('estate_address')['zip_'] = data.get('estate_address').pop('zip')
                if data.get('floor') is not None:
                    data.get('floor')['id_'] = data.get('floor').pop('id')
                ret_la = UseUnit(**data)
                retlist.append(ret_la)
        return retlist

    def get_contractors(self,
                        license_agreement_id: int = None,
                        person_id: int = None,
                        license_agreement_active_on: datetime = None,
                        contractual_use_active_on: datetime = None,
                        limit: int = None,
                        offset: int = 0,
                        add_args: Dict = None,
                        use_cache: bool = False) -> List[Contractor]:
        """
        Gibt eine Liste von Vertragsnehmern zurück
        :param use_cache:
        :type use_cache:
        :param contractual_use_active_on: (Optional) Nur Vertragsnehmer, deren ContractUse zu diesem Zeitpunkt aktiv war
        :type contractual_use_active_on: datetime
        :param license_agreement_active_on: (Optional) Nur Contractors deren Vertrag zu diesem Datum aktiv ist
        :type license_agreement_active_on: datetime
        :param person_id: (Optional) Alle Contractor-Beziehungen zu dieser internen Personen-ID
        :type person_id: int
        :param license_agreement_id: Alle Contractor-Beziehungen zu dieser internen Vertrags-ID
        :type license_agreement_id: int
        :param limit: Maximale Anzahl an Einträgen, die zurückgegeben werden (max = default = 100)
        :type limit: int
        :param offset: (Optional) Verschiebung der Abfrage. Default: 0
        :type offset: int
        :param add_args: Zusätzliche Parameter, die per GET an die URL angehängt werden
        :type add_args: Dict
        :return: Liste aus Contractor (auch bei nur einem Ergebnis!)
        :rtype: List[Contractor]
        """
        filter_params = {}
        if license_agreement_id is not None:
            filter_params['licenseAgreementId'] = license_agreement_id
        if person_id is not None:
            filter_params['personId'] = person_id
        if license_agreement_active_on is not None:
            filter_params['licenseAgreementActiveOn'] = license_agreement_active_on
        if contractual_use_active_on is not None:
            filter_params['contractualUseActiveOn'] = contractual_use_active_on
        if limit is not None:
            filter_params['limit'] = limit
        filter_params['offset'] = offset

        # Standardparameter, können via add_args überschrieben werden
        filter_params['includeMainAddress'] = 'true'
        filter_params['includeMainCommunication'] = 'true'
        filter_params['includePersonAddresses'] = 'true'
        filter_params['includePersonCommunications'] = 'true'
        filter_params['includePersonBankAccounts'] = 'true'
        filter_params['showNullValues'] = 'true'

        if add_args is not None:
            filter_params.update(add_args)

        retlist = []
        if use_cache:
            cache_entry: Contractor
            for cache_entry in self._cache[self.CACHE_CONTRACTORS]:
                if (license_agreement_id is not None and cache_entry.license_agreement_id == license_agreement_id) or \
                        (person_id is not None and cache_entry.person.id_ == person_id):
                    retlist.append(copy.deepcopy(cache_entry))
        else:
            result = self._rest_adapter.get(endpoint='RentAccountingPersonDetails/Contractors', ep_params=filter_params)

            for entry in result.data:
                data = dict(humps.decamelize(entry))
                data['id_'] = data.pop('id')
                ret_la = Contractor(**data)
                retlist.append(ret_la)
        return retlist

    def get_persons(self,
                    person_id: int = None,
                    limit: int = None,
                    offset: int = 0,
                    add_args: Dict = None,
                    use_cache: bool = False) -> List[Person]:

        filter_params = {}
        if person_id is not None:
            filter_params['personId'] = person_id
        if limit is not None:
            filter_params['limit'] = limit
        filter_params['offset'] = offset

        # Standardparameter, können via add_args überschrieben werden
        filter_params['includeAddress'] = 'true'
        filter_params['includeCommunication'] = 'true'
        filter_params['includeBankccount'] = 'true'
        filter_params['showNullValues'] = 'true'

        if add_args is not None:
            filter_params.update(add_args)

        retlist = []
        if use_cache:
            cache_entry: Person
            for cache_entry in self._cache[self.CACHE_PERSONS]:
                if person_id is not None and cache_entry.id_ == person_id:
                    retlist.append(copy.deepcopy(cache_entry))
        else:
            result = self._rest_adapter.get(endpoint='PersonsRead/Persons', ep_params=filter_params)

            for entry in result.data:
                data = dict(humps.decamelize(entry))
                data['id_'] = data.pop('id')
                data['shortname'] = data.pop('short_name')

                # Der nächste Part ist notwendig, weil das Ergebnis der Route aktuell leicht von der Doku abweicht.
                # Laut Doku gibt es das Feld IsNaturalPerson (bool), dieses wird aber nicht ausgegeben.
                # Der Workaround ist nun das Auslesen von NaturalPerson[Gender]. Steht es auf id 3 (nicht angegeben),
                # wird die Person als "nicht natürlich" angesehen.
                workaround_is_nat_person = False
                workaround_gender = data['natural_person'].get("gender")
                if workaround_gender is not None:
                    workaround_gender_id = int(workaround_gender.get("id"))
                    if workaround_gender_id != 3:
                        workaround_is_nat_person = True
                data['is_natural_person'] = workaround_is_nat_person
                # Workaround für natürliche Person Ende
                ret_per = Person(**data)
                retlist.append(ret_per)
        return retlist

    def get_contract_positions(self,
                               license_agreement_idnum: str = None,
                               license_agreement_id: int = None,
                               contract_positions_active_on: datetime = None,
                               limit: int = None,
                               offset: int = 0,
                               add_args: Dict = None) -> List[ContractPosition]:

        filter_params = {}
        if license_agreement_idnum is not None:
            filter_params['licenseAgreementIdNum'] = license_agreement_idnum
        if license_agreement_id is not None:
            filter_params['licenseAgreementId'] = license_agreement_id
        if contract_positions_active_on is not None:
            filter_params['contractPositionsActiveOn'] = contract_positions_active_on.strftime("%Y-%m-%d")
        if limit is not None:
            filter_params['limit'] = limit
        filter_params['offset'] = offset

        filter_params['includeContractPositionTypeDetails'] = 'true'
        filter_params['showNullValues'] = 'true'

        if add_args is not None:
            filter_params.update(add_args)

        retlist = []
        result = self._rest_adapter.get(endpoint='RentAccounting/ContractPositions', ep_params=filter_params)

        for entry in result.data:
            data = dict(humps.decamelize(entry))
            data['id_'] = data.pop('id')
            ret_la = ContractPosition(**data)
            retlist.append(ret_la)

        return retlist

    def get_tickets(self,
                    ticket_id: int = None,
                    ticket_id_num: str = None,
                    ticket_priority_id: int = None,
                    ticket_status_id: int = None,
                    ticket_source_id: int = None,
                    limit: int = None,
                    offset: int = 0,
                    add_args: Dict = None
                    ) -> List[Ticket]:

        filter_params = {}
        if ticket_id is not None:
            filter_params['ticketId'] = ticket_id
        if ticket_id_num is not None:
            filter_params['ticketIdNum'] = ticket_id_num
        if ticket_priority_id is not None:
            filter_params['ticketPriorityId'] = ticket_priority_id
        if ticket_status_id is not None:
            filter_params['ticketStatusId'] = ticket_status_id
        if ticket_source_id is not None:
            filter_params['ticketSourceId'] = ticket_source_id

        if limit is not None:
            filter_params['limit'] = limit
        filter_params['offset'] = offset

        # Standardparameter, können via add_args überschrieben werden
        filter_params['includeComments'] = 'true'
        filter_params['includeAssignmentEntity'] = 'true'
        filter_params['showNullValues'] = 'true'

        if add_args is not None:
            filter_params.update(add_args)

        retlist = []

        result = self._rest_adapter.get(endpoint='CommunicationRead/Ticket', ep_params=filter_params)
        for entry in result.data:
            data = dict(humps.decamelize(entry))
            data['id_'] = data.pop('id')
            ret_la = Ticket(**data)
            retlist.append(ret_la)

        return retlist

    def get_communication_catalogs(self) -> CommunicationCatalog:
        cat_ass = self._rest_adapter.get(endpoint='CommunicationCatalog/TicketAssignmentEntity').data
        cat_prio = self._rest_adapter.get(endpoint='CommunicationCatalog/TicketPriority').data
        cat_source = self._rest_adapter.get(endpoint='CommunicationCatalog/TicketSource').data
        cat_status = self._rest_adapter.get(endpoint='CommunicationCatalog/TicketStatus').data

        cat_list = [
            cat_ass,
            cat_prio,
            cat_source,
            cat_status
        ]

        return CommunicationCatalog(cat_list)

    def create_ticket(self,
                      subject: str,
                      content: str,
                      source_id: int,
                      main_assignment: TicketAssignment = None,
                      assignments: List[TicketAssignment] = None,
                      department_id: int = None,
                      user_id: int = None,
                      priority_id: int = 1
                      ) -> Result:
        data_dict = {
            "Subject": subject,
            "Content": content,
            "SourceId": source_id,
            "PriorityId": priority_id,
        }
        if department_id is not None:
            data_dict["DepartmentId"] = department_id
        if user_id is not None:
            data_dict["UserId"] = user_id

        data_dict["MainEntityAssignment"] = None
        if main_assignment is not None:
            tmain_ass = {
                "AssignmentEntityId": main_assignment.assignment_entity_id,
                "EntityId": main_assignment.entity_id
            }
            data_dict["MainEntityAssignment"] = tmain_ass

        if assignments is not None and len(assignments) > 0:
            asslist = []
            for tentry in assignments:
                tass = {
                    "AssignmentEntityId": tentry.assignment_entity_id,
                    "EntityId": tentry.entity_id
                }
                asslist.append(tass)
            if len(asslist) > 0:
                data_dict["EntityAssignments"] = asslist
        print(f"MAIN: {data_dict['MainEntityAssignment']}")
        result = self._rest_adapter.post(endpoint='CommunicationEdit/Ticket', data=data_dict)
        return result

    def create_ticket_comment(self,
                              ticket_id: int,
                              content: str
                              ) -> Result:
        data_dict = {
            "TicketId": ticket_id,
            "Content": content
        }

        result = self._rest_adapter.post(endpoint='CommunicationEdit/Ticket/AddComment', data=data_dict)
        return result
