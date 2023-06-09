import copy
import logging
import humps
import pickle
from wowipy.rest_adapter import RestAdapter
from wowipy.exceptions import WowiPyException
from wowipy.models import *


class WowiPy:
    CACHE_LICENSE_AGREEMENTS = "license_agreements"
    CACHE_CONTRACTORS = "contractors"
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
                                           economic_idnum=economic_idnum,
                                           add_args=add_args, limit=limit, offset=offset)
        response_len = len(ret_list)

        while response_len == limit:
            offset += limit
            t_resp = self.get_building_lands(management_idnum=management_idnum,
                                             owner_number=owner_number,
                                             economic_idnum=economic_idnum,
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
                           economic_idnum: str = None,
                           building_land_idnum: str = None,
                           limit: int = None,
                           offset: int = 0,
                           add_args: Dict = None) -> List[BuildingLand]:
        """
        Gibt ein oder mehrere Gebäude als Liste zurück.
        :param offset: Verschiebung der Abfrage. Default: 0
        :type offset: int
        :param management_idnum: (Optional) Nur Gebäude dieses Managements zurückgeben
        :type management_idnum: str
        :param owner_number: (Optional) Nur Gebäude dieses Eigentümers zurückgeben
        :type owner_number: str
        :param economic_idnum: (Optional) Nur Gebäude dieser Wirtschaftseinheit zurückgeben
        :type economic_idnum: str
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
        if economic_idnum is not None:
            filter_params['economicIdNum'] = economic_idnum
        if building_land_idnum is not None:
            filter_params['buildingLandIdNum'] = building_land_idnum
        if limit is not None:
            filter_params['limit'] = limit
        filter_params['offset'] = offset

        # Ein paar Standardwerte, können aber durch add_args überschrieben werden
        filter_params['includeCompanyCode'] = 'true'

        if add_args is not None:
            filter_params.update(add_args)

        result = self._rest_adapter.get(endpoint='CommercialInventory/BuildingLands', ep_params=filter_params)
        retlist = []
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

    def get_use_units(self,
                      use_unit_idnum: str = None,
                      building_land_idnum: str = None,
                      economic_unit_idnum: str = None,
                      management_idnum: str = None,
                      owner_number: str = None,
                      limit: int = None,
                      offset: int = 0,
                      add_args: Dict = None) -> List[UseUnit]:
        """
        Gibt eine Liste von Nutzungseinheiten zurück
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
            filter_params['useUnitNumber'] = owner_number
        if building_land_idnum is not None:
            filter_params['buildingLandIdNum'] = owner_number
        if economic_unit_idnum is not None:
            filter_params['EconomicUnitIdNum'] = owner_number
        if management_idnum is not None:
            filter_params['managementIdNum'] = owner_number
        if owner_number is not None:
            filter_params['ownerNumber'] = owner_number
        if limit is not None:
            filter_params['limit'] = limit
        filter_params['offset'] = offset

        # Standardparameter, können via add_args überschrieben werden
        filter_params['includeUseUnitTypes'] = 'true'
        filter_params['includeBillingUnits'] = 'true'
        filter_params['includeMarketingTags'] = 'false'

        if add_args is not None:
            filter_params.update(add_args)

        result = self._rest_adapter.get(endpoint='CommercialInventory/UseUnits', ep_params=filter_params)
        retlist = []
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
