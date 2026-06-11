import copy
import logging
import humps
import pickle
import base64
import hashlib
import os
from jsonmerge import Merger
from wowipy.rest_adapter import RestAdapter
from wowipy.exceptions import WowiPyException
from wowipy.models import *


def file_to_base64(file_path):
    with open(file_path, "rb") as file:
        encoded_string = base64.b64encode(file.read()).decode('utf-8')
    return encoded_string


def sha1sum(filename):
    h = hashlib.sha1()
    b = bytearray(128 * 1024)
    mv = memoryview(b)
    with open(filename, 'rb', buffering=0) as f:
        # noinspection PyUnresolvedReferences
        while n := f.readinto(mv):
            h.update(mv[:n])
    return h.hexdigest()


class WowiPy:
    CACHE_LICENSE_AGREEMENTS = "license_agreements"
    CACHE_CONTRACTORS = "contractors"
    CACHE_PERSONS = "persons"
    CACHE_ECONOMIC_UNITS = "license_agreements"
    CACHE_BUILDING_LANDS = "building_lands"
    CACHE_USE_UNITS = "use_units"
    CACHE_CONTRACT_POSITIONS = "contract_positions"

    SEARCH_POS_LEFT = "begins"
    SEARCH_POS_CONTAINS = "contains"

    def __init__(self, hostname: str, user: str, password: str, api_key: str, version: str = 'v1.2',
                 logger: logging.Logger = None, user_agent: str = "WowiPy/1.1"):
        self._rest_adapter = RestAdapter(hostname, user, password, api_key, version, logger, user_agent)
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
                    # haystack = {
                    #     sobj.id_num
                    # }
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

    def build_contract_position_cache(self,
                                      contract_position_active_on: datetime = None) -> None:

        all_positions = self.get_all_contract_positions(contract_positions_active_on=contract_position_active_on)
        self._cache[self.CACHE_CONTRACT_POSITIONS] = all_positions

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
                               limit: int = 100,
                               offset: int = 0,
                               add_args: Dict = None,
                               add_contractors: bool = False,
                               fetch_all: bool = False,
                               ) -> List[LicenseAgreement]:

        filter_params = {}
        if economic_unit_idnum:
            filter_params['EconomicUnitIdNum'] = economic_unit_idnum
        if use_unit_idnum:
            filter_params['UseUnitNumber'] = use_unit_idnum
        if license_agreement_idnum:
            filter_params['LicenseAgreementIdNum'] = license_agreement_idnum
        if license_agreement_active_on:
            filter_params['licenseAgreementActiveOn'] = license_agreement_active_on.strftime("%Y-%m-%d")
        if person_idnum:
            filter_params['personIdNum'] = person_idnum

        filter_params['limit'] = limit
        filter_params['offset'] = offset
        filter_params['showNullValues'] = 'true'
        filter_params['includeBanking'] = 'true'
        if add_args is not None:
            filter_params.update(add_args)

        retlist = []
        if not fetch_all:
            result = self._rest_adapter.get(endpoint='RentAccounting/LicenseAgreements', ep_params=filter_params)
        else:
            result = Result(0, "", [])
            merge_schema = {"mergeStrategy": "append"}
            merger = Merger(schema=merge_schema)
            filter_params['offset'] = 0
            filter_params['limit'] = 100
            response_count = 100
            while response_count == 100:
                part_result = self._rest_adapter.get(endpoint='RentAccounting/LicenseAgreements',
                                                     ep_params=filter_params)
                result.data = merger.merge(result.data, part_result.data)
                filter_params['offset'] += 100
                response_count = len(part_result.data)
                print(f"License-Agreement-Count: {len(result.data)}")

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

    def get_online_repayment_plan(self, loan_id: int):
        result = self._rest_adapter.get(endpoint=f'Loans/Loan/{loan_id}/OnlineRepaymentPlan')
        retlist = []
        for entry in result.data:
            data = dict(humps.decamelize(entry))
            ret_la = OnlineRepaymentPlanEntry(**data)
            retlist.append(ret_la)
        return retlist

    def get_repayment_plan(self, loan_id: int):
        result = self._rest_adapter.get(endpoint=f'Loans/Loan/{loan_id}/RepaymentPlan')
        retlist = []
        for entry in result.data:
            data = dict(humps.decamelize(entry))
            data["id_"] = data.pop("id")
            ret_la = RepaymentPlanEntry(**data)
            retlist.append(ret_la)
        return retlist

    def get_loans(self,
                  loan_id: int = None,
                  loan_idnum: str = None,
                  loan_type_id: int = None,
                  company_code_id: int = None,
                  lender_id: int = None,
                  lender_idnum: str = None,
                  borrower_id: int = None,
                  borrower_idnum: str = None,
                  limit: int = None,
                  offset: int = 0,
                  add_args: Dict = None,
                  fetch_all: bool = False
                  ) -> List[Loan]:
        filter_params = {}
        if loan_id is not None:
            filter_params['loanId'] = loan_id
        if loan_idnum is not None:
            filter_params['loanIdNum'] = loan_idnum
        if loan_type_id is not None:
            filter_params['loanTypeId'] = loan_type_id
        if company_code_id is not None:
            filter_params['companyCodeId'] = company_code_id
        if lender_id is not None:
            filter_params['lenderId'] = lender_id
        if lender_idnum is not None:
            filter_params['lenderNumber'] = lender_idnum
        if borrower_id is not None:
            filter_params['borrowerId'] = borrower_id
        if borrower_idnum is not None:
            filter_params['borrowerNumber'] = borrower_idnum
        if limit is not None:
            filter_params['limit'] = limit
        filter_params['offset'] = offset
        filter_params['includeBanking'] = 'true'
        filter_params['includeObjectAssignment'] = 'true'
        filter_params['includeCondition'] = 'true'
        filter_params['includeRepaymentPlan'] = 'true'
        filter_params['includeAdditionalField'] = 'true'
        filter_params['showNullValues'] = 'true'

        if add_args is not None:
            filter_params.update(add_args)
        retlist = []
        if not fetch_all:
            result = self._rest_adapter.get(endpoint='Loans/Loan', ep_params=filter_params)
        else:
            result = Result(0, "", [])
            merge_schema = {"mergeStrategy": "append"}
            merger = Merger(schema=merge_schema)
            filter_params['offset'] = 0
            filter_params['limit'] = 100
            response_count = 100
            while response_count == 100:
                part_result = self._rest_adapter.get(endpoint='Loans/Loan',
                                                     ep_params=filter_params)
                result.data = merger.merge(result.data, part_result.data)
                filter_params['offset'] += 100
                response_count = len(part_result.data)
                print(f"Loan-Count: {len(result.data)}")

        for entry in result.data:
            data = dict(humps.decamelize(entry))
            data['id_'] = data.pop('id')
            ret_la = Loan(**data)
            retlist.append(ret_la)
        return retlist

    def get_economic_units(self,
                           management_idnum: str = None,
                           owner_number: str = None,
                           economic_unit_idnum: str = None,
                           economic_unit_id: int = None,
                           limit: int = None,
                           offset: int = 0,
                           add_args: Dict = None,
                           fetch_all: bool = False) -> List[EconomicUnit]:

        filter_params = {}
        if management_idnum is not None:
            filter_params['managementIdNum'] = management_idnum
        if owner_number is not None:
            filter_params['ownerNumber'] = owner_number
        if economic_unit_idnum is not None:
            filter_params['economicUnitIdNum'] = economic_unit_idnum
        if economic_unit_id is not None:
            filter_params['economicUnitId'] = economic_unit_id
        if limit is not None:
            filter_params['limit'] = limit
        filter_params['offset'] = offset

        # Ein paar Standardwerte, können aber durch add_args überschrieben werden
        filter_params['includeCompanyCode'] = 'true'

        if add_args is not None:
            filter_params.update(add_args)
        retlist = []
        if not fetch_all:
            result = self._rest_adapter.get(endpoint='CommercialInventory/EconomicUnits', ep_params=filter_params)
        else:
            result = Result(0, "", [])
            merge_schema = {"mergeStrategy": "append"}
            merger = Merger(schema=merge_schema)
            filter_params['offset'] = 0
            filter_params['limit'] = 100
            response_count = 100
            while response_count == 100:
                part_result = self._rest_adapter.get(endpoint='CommercialInventory/EconomicUnits',
                                                     ep_params=filter_params)
                result.data = merger.merge(result.data, part_result.data)
                filter_params['offset'] += 100
                response_count = len(part_result.data)
                print(f"Economic-Unit-Count: {len(result.data)}")

        for entry in result.data:
            data = dict(humps.decamelize(entry))
            data['id_'] = data.pop('id')
            ret_la = EconomicUnit(**data)
            retlist.append(ret_la)
        return retlist

    def get_building_lands(self,
                           management_idnum: str = None,
                           management_id: int = None,
                           owner_number: str = None,
                           owner_id: int = None,
                           economic_unit_idnum: str = None,
                           economic_unit_id: int = None,
                           building_land_idnum: str = None,
                           building_land_id: int = None,
                           building_land_type: str = None,
                           limit: int = None,
                           offset: int = 0,
                           add_args: Dict = None,
                           fetch_all: bool = False,
                           use_cache: bool = False) -> List[BuildingLand]:

        filter_params = {}
        if management_idnum is not None:
            filter_params['managementIdNum'] = management_idnum
        if management_id is not None:
            filter_params['managementId'] = management_id
        if owner_number is not None:
            filter_params['ownerNumber'] = owner_number
        if owner_id is not None:
            filter_params['ownerId'] = owner_number
        if economic_unit_idnum is not None:
            filter_params['economicUnitIdNum'] = economic_unit_idnum
        if economic_unit_id is not None:
            filter_params['economicUnitId'] = economic_unit_id
        if building_land_idnum is not None:
            filter_params['buildingLandIdNum'] = building_land_idnum
        if building_land_id is not None:
            filter_params['buildingLandId'] = building_land_id
        if building_land_type is not None:
            filter_params['buildingLandType'] = building_land_type
        if limit is not None:
            filter_params['limit'] = limit
        filter_params['offset'] = offset

        # Ein paar Standardwerte, können aber durch add_args überschrieben werden
        filter_params['includeCompanyCode'] = 'true'
        filter_params['showNullValues'] = 'true'
        filter_params['includeAdditionalField'] = 'true'

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
                      fetch_all: bool = False,
                      use_cache: bool = False,
                      use_unit_id: int = None) -> List[UseUnit]:

        filter_params = {}
        if use_unit_idnum is not None:
            filter_params['useUnitNumber'] = use_unit_idnum
        if use_unit_id is not None:
            filter_params['useUnitId'] = use_unit_id
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
            if not fetch_all:
                result = self._rest_adapter.get(endpoint='CommercialInventory/UseUnits', ep_params=filter_params)
            else:
                result = Result(0, "", [])
                merge_schema = {"mergeStrategy": "append"}
                merger = Merger(schema=merge_schema)
                filter_params['offset'] = 0
                filter_params['limit'] = 100
                response_count = 100
                while response_count == 100:
                    part_result = self._rest_adapter.get(endpoint='CommercialInventory/UseUnits',
                                                         ep_params=filter_params)
                    result.data = merger.merge(result.data, part_result.data)
                    filter_params['offset'] += 100
                    response_count = len(part_result.data)
                    print(f"UseUnit-Count: {len(result.data)}")

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
                        fetch_all: bool = False,
                        use_cache: bool = False) -> List[Contractor]:

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
            if not fetch_all:
                result = self._rest_adapter.get(endpoint='RentAccountingPersonDetails/Contractors',
                                                ep_params=filter_params)
            else:
                result = Result(0, "", [])
                merge_schema = {"mergeStrategy": "append"}
                merger = Merger(schema=merge_schema)
                filter_params['offset'] = 0
                filter_params['limit'] = 100
                response_count = 100
                while response_count == 100:
                    part_result = self._rest_adapter.get(endpoint='RentAccountingPersonDetails/Contractors',
                                                         ep_params=filter_params)
                    result.data = merger.merge(result.data, part_result.data)
                    filter_params['offset'] += 100
                    response_count = len(part_result.data)
                    print(f"Contractors-Count: {len(result.data)}")

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
                    fetch_all: bool = False,
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
            if not fetch_all:
                result = self._rest_adapter.get(endpoint='PersonsRead/Persons', ep_params=filter_params)
            else:
                result = Result(0, "", [])
                merge_schema = {"mergeStrategy": "append"}
                merger = Merger(schema=merge_schema)
                filter_params['offset'] = 0
                filter_params['limit'] = 100
                response_count = 100
                while response_count == 100:
                    part_result = self._rest_adapter.get(endpoint='PersonsRead/Persons',
                                                         ep_params=filter_params)
                    result.data = merger.merge(result.data, part_result.data)
                    filter_params['offset'] += 100
                    response_count = len(part_result.data)
                    print(f"Person-Count: {len(result.data)}")

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

    def get_all_contract_positions(self,
                                   contract_positions_active_on: datetime = None,
                                   use_cache: bool = False) -> List[ContractPosition]:
        if use_cache:
            return self._cache[self.CACHE_CONTRACT_POSITIONS]

        result = Result(0, "", [])
        merge_schema = {"mergeStrategy": "append"}
        merger = Merger(schema=merge_schema)
        offset = 0
        limit = 100
        response_count = 100

        while response_count == 100:
            part_result = self.get_contract_positions(contract_positions_active_on=contract_positions_active_on,
                                                      limit=limit, offset=offset)
            result.data = merger.merge(result.data, part_result)
            offset += 100
            response_count = len(part_result)
            print(f"Contract Position Count: {len(result.data)}")

        return result.data

    def get_districts(self) -> List[District]:
        retlist = []
        result = self._rest_adapter.get(endpoint='CommercialInventoryCatalog/Districts')

        for entry in result.data:
            data = dict(humps.decamelize(entry))
            data['id_'] = data.pop('id')
            ret_la = District(**data)
            retlist.append(ret_la)

        return retlist

    def get_building_types(self) -> List[BuildingType]:
        retlist = []
        result = self._rest_adapter.get(endpoint='CommercialInventoryCatalog/BuildingTypes')

        for entry in result.data:
            data = dict(humps.decamelize(entry))
            data['id_'] = data.pop('id')
            ret_la = BuildingType(**data)
            retlist.append(ret_la)

        return retlist

    def get_use_unit_types(self) -> List[UseUnitTypeCatalogEntry]:
        retlist = []
        result = self._rest_adapter.get(endpoint='CommercialInventoryCatalog/UseUnitType')

        for entry in result.data:
            data = dict(humps.decamelize(entry))
            data['id_'] = data.pop('id')
            ret_la = UseUnitTypeCatalogEntry(**data)
            retlist.append(ret_la)

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

    def get_departments(self,
                        department_id: int = None,
                        department_name: str = None,
                        limit: int = 100,
                        offset: int = 0) -> List[Department]:
        filter_params = {}
        if department_id:
            filter_params['departmentId'] = department_id
        if department_name:
            filter_params['departmentName'] = department_name
        filter_params['limit'] = limit
        filter_params['offset'] = offset
        filter_params['showNullValues'] = 'true'

        retlist = []

        result = self._rest_adapter.get(endpoint='CommercialInventory/Department', ep_params=filter_params,
                                        force_refresh=True)
        for entry in result.data:
            data = dict(humps.decamelize(entry))
            data['id_'] = data.pop('id')
            data['type_id'] = data['department_type'].pop('id')
            data['type_name'] = data['department_type'].pop('name')
            ret_la = Department(**data)
            retlist.append(ret_la)

        return retlist

    def get_payment_modes(self,
                          license_agreement_id: int = None,
                          license_agreement_idnum: str = None,
                          payment_mode_active_on: datetime = None,
                          license_agreement_active_on: datetime = None,
                          limit: int = 100,
                          offset: int = 0,
                          fetch_all: bool = False,
                          add_args: Dict = None) -> List[PaymentMode]:
        filter_params = {}
        if license_agreement_id:
            filter_params['licenseAgreementId'] = license_agreement_id
        if license_agreement_idnum:
            filter_params['licenseAgreementIdNum'] = license_agreement_idnum
        if payment_mode_active_on:
            filter_params['paymentModeActiveOn'] = payment_mode_active_on.strftime("%Y-%m-%d")
        if license_agreement_active_on:
            filter_params['licenseAgreementActiveOn'] = license_agreement_active_on.strftime("%Y-%m-%d")

        filter_params['limit'] = limit
        filter_params['offset'] = offset
        filter_params['showNullValues'] = 'true'

        if add_args is not None:
            filter_params.update(add_args)

        retlist = []

        if not fetch_all:
            result = self._rest_adapter.get(endpoint='RentAccountingPersonDetails/PaymentModes',
                                            ep_params=filter_params,
                                            force_refresh=True)
        else:
            result = Result(0, "", [])
            merge_schema = {"mergeStrategy": "append"}
            merger = Merger(schema=merge_schema)
            filter_params['offset'] = 0
            filter_params['limit'] = 100
            response_count = 100
            while response_count == 100:
                part_result = self._rest_adapter.get(endpoint='RentAccountingPersonDetails/PaymentModes',
                                                     ep_params=filter_params,
                                                     force_refresh=True)
                result.data = merger.merge(result.data, part_result.data)
                filter_params['offset'] += 100
                response_count = len(part_result.data)
                print(f"Payment-Mode-Count: {len(result.data)}")

        for entry in result.data:
            data = dict(humps.decamelize(entry))
            data['id_'] = data.pop('id')

            ret_per = PaymentMode(**data)
            retlist.append(ret_per)

        return retlist

    def get_tickets(self,
                    ticket_id: int = None,
                    ticket_id_num: str = None,
                    ticket_priority_id: int = None,
                    ticket_status_id: int = None,
                    ticket_source_id: int = None,
                    limit: int = None,
                    offset: int = 0,
                    add_args: Dict = None,
                    force_refresh: bool = False,
                    fetch_all: bool = False,
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

        if not fetch_all:
            result = self._rest_adapter.get(endpoint='CommunicationRead/Ticket', ep_params=filter_params,
                                            force_refresh=force_refresh)
        else:
            result = Result(0, "", [])
            merge_schema = {"mergeStrategy": "append"}
            merger = Merger(schema=merge_schema)
            filter_params['offset'] = 0
            filter_params['limit'] = 100
            response_count = 100
            while response_count == 100:
                part_result = self._rest_adapter.get(endpoint='CommunicationRead/Ticket', ep_params=filter_params,
                                                     force_refresh=force_refresh)
                result.data = merger.merge(result.data, part_result.data)
                filter_params['offset'] += 100
                response_count = len(part_result.data)
                print(f"Ticket-Count: {len(result.data)}")
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

    def get_responsible_officials(self,
                                  user_id: int = None,
                                  person_id: int = None,
                                  limit: int = None,
                                  offset: int = 0,
                                  add_args: Dict = None,
                                  fetch_all: bool = False
                                  ) -> List[ResponsibleOfficial]:

        filter_params = {}

        if person_id is not None:
            filter_params['personId'] = person_id

        if limit is not None:
            filter_params['limit'] = limit
        filter_params['offset'] = offset

        # Standardparameter, können via add_args überschrieben werden
        filter_params['showNullValues'] = 'true'
        filter_params['includePersonCommunications'] = 'true'
        filter_params['includeMainCommunication'] = 'true'

        if add_args is not None:
            filter_params.update(add_args)

        retlist = []

        if not fetch_all:
            result = self._rest_adapter.get(endpoint='CommercialInventory/ResponsibleOfficial',
                                            ep_params=filter_params)
        else:
            result = Result(0, "", [])
            merge_schema = {"mergeStrategy": "append"}
            merger = Merger(schema=merge_schema)
            filter_params['offset'] = 0
            filter_params['limit'] = 100
            response_count = 100
            while response_count == 100:
                part_result = self._rest_adapter.get(endpoint='CommercialInventory/ResponsibleOfficial',
                                                     ep_params=filter_params)
                result.data = merger.merge(result.data, part_result.data)
                filter_params['offset'] += 100
                response_count = len(part_result.data)
                print(f"ResponsibleOfficial Count: {len(result.data)}")

        for entry in result.data:
            data = dict(humps.decamelize(entry))
            if user_id is not None and data.get("user_id") != user_id:
                continue
            # Hier hängt normalerweise noch die Person dran. Die wollen wir aber nicht mitnehmen (jedenfalls
            # aktuell nicht) um die Ausgabe an die der Jurisdictions anzugleichen
            # Default Address wird auch entfernt
            try:
                data.pop("default_address", None)
                tperson = data.get("person")
                data["person_id"] = tperson.get("id", None)
                data["person_name"] = tperson.get("name", None)
                data["id_"] = data.pop("id")
                ret_la = ResponsibleOfficial(**data)
                retlist.append(ret_la)
            except KeyError:
                pass

        return retlist

    def get_economic_unit_jurisdictions(self,
                                        economic_unit_id: int = None,
                                        limit: int = None,
                                        offset: int = 0,
                                        add_args: Dict = None,
                                        fetch_all: bool = False
                                        ) -> List[EconomicUnitJurisdiction]:

        filter_params = {}
        if economic_unit_id is not None:
            filter_params['economicUnitId'] = economic_unit_id

        if limit is not None:
            filter_params['limit'] = limit
        filter_params['offset'] = offset

        # Standardparameter, können via add_args überschrieben werden
        filter_params['showNullValues'] = 'true'

        if add_args is not None:
            filter_params.update(add_args)

        retlist = []

        if not fetch_all:
            result = self._rest_adapter.get(endpoint='CommercialInventory/EconomicUnit/Jurisdiction',
                                            ep_params=filter_params)
        else:
            result = Result(0, "", [])
            merge_schema = {"mergeStrategy": "append"}
            merger = Merger(schema=merge_schema)
            filter_params['offset'] = 0
            filter_params['limit'] = 100
            response_count = 100
            while response_count == 100:
                part_result = self._rest_adapter.get(endpoint='CommercialInventory/EconomicUnit/Jurisdiction',
                                                     ep_params=filter_params)
                result.data = merger.merge(result.data, part_result.data)
                filter_params['offset'] += 100
                response_count = len(part_result.data)
                print(f"Eco-Jurisdiction-Count: {len(result.data)}")

        for entry in result.data:
            data = dict(humps.decamelize(entry))
            ret_la = EconomicUnitJurisdiction(**data)
            retlist.append(ret_la)

        return retlist

    def get_use_unit_jurisdictions(self,
                                   use_unit_id: int = None,
                                   economic_unit_id: int = None,
                                   limit: int = None,
                                   offset: int = 0,
                                   add_args: Dict = None,
                                   fetch_all: bool = False
                                   ) -> List[UseUnitJurisdiction]:

        filter_params = {}
        if economic_unit_id is not None:
            filter_params['economicUnitId'] = economic_unit_id
        if use_unit_id is not None:
            filter_params['useUnitId'] = use_unit_id

        if limit is not None:
            filter_params['limit'] = limit
        filter_params['offset'] = offset

        # Standardparameter, können via add_args überschrieben werden
        filter_params['showNullValues'] = 'true'

        if add_args is not None:
            filter_params.update(add_args)

        retlist = []

        if not fetch_all:
            result = self._rest_adapter.get(endpoint='CommercialInventory/UseUnit/Jurisdiction',
                                            ep_params=filter_params)
        else:
            result = Result(0, "", [])
            merge_schema = {"mergeStrategy": "append"}
            merger = Merger(schema=merge_schema)
            filter_params['offset'] = 0
            filter_params['limit'] = 100
            response_count = 100
            while response_count == 100:
                part_result = self._rest_adapter.get(endpoint='CommercialInventory/UseUnit/Jurisdiction',
                                                     ep_params=filter_params)
                result.data = merger.merge(result.data, part_result.data)
                filter_params['offset'] += 100
                response_count = len(part_result.data)
                print(f"UseUnit-Jurisdiction-Count: {len(result.data)}")

        for entry in result.data:
            data = dict(humps.decamelize(entry))
            ret_la = UseUnitJurisdiction(**data)
            retlist.append(ret_la)

        return retlist

    def get_file_type_catalog(self):
        retlist = []
        result = self._rest_adapter.get(endpoint='DocumentReadCatalog/FileType')
        for entry in result.data:
            data = dict(humps.decamelize(entry))
            data['id_'] = data.pop('id')
            ret_la = FileType(**data)
            retlist.append(ret_la)

        return retlist

    def get_picture_type_catalog(self):
        retlist = []
        result = self._rest_adapter.get(endpoint='MediaReadCatalog/EstatePictureType')
        for entry in result.data:
            data = dict(humps.decamelize(entry))
            data['id_'] = data.pop('id')
            ret_la = PictureType(**data)
            retlist.append(ret_la)

        return retlist

    def get_file_entity_catalog(self):
        retlist = []
        result = self._rest_adapter.get(endpoint='DocumentReadCatalog/FileEntity')

        for entry in result.data:
            data = dict(humps.decamelize(entry))
            data['id_'] = data.pop('id')
            ret_la = FileEntity(**data)
            retlist.append(ret_la)

        return retlist

    def get_media_entity_catalog(self):
        retlist = []
        result = self._rest_adapter.get(endpoint='MediaReadCatalog/MediaEntity')

        for entry in result.data:
            data = dict(humps.decamelize(entry))
            data['id_'] = data.pop('id')
            ret_la = MediaEntity(**data)
            retlist.append(ret_la)

        return retlist

    def get_file_entity_id_from_name(self, file_entity_name: str) -> int:
        file_entity_cat = self.get_file_entity_catalog()
        for entity_cat in file_entity_cat:
            if entity_cat.name.lower() == file_entity_name:
                return entity_cat.id_
        return 0

    def get_file_entity_name_from_id(self, file_entity_id: int) -> str:
        file_entity_cat = self.get_file_entity_catalog()
        for entity_cat in file_entity_cat:
            if entity_cat.id_ == file_entity_id:
                return entity_cat.name
        return ""

    def get_media_entity_id_from_name(self, media_entity_name: str) -> int:
        media_entity_cat = self.get_media_entity_catalog()
        for med_cat in media_entity_cat:
            if med_cat.name.lower() == media_entity_name:
                return med_cat.id_
        return 0

    def get_media_entity_name_from_id(self, media_entity_id: int) -> str:
        media_entity_cat = self.get_media_entity_catalog()
        for med_cat in media_entity_cat:
            if med_cat.id_ == media_entity_id:
                return med_cat.name
        return ""

    def get_file_type_id_from_name(self, file_type_name: str) -> int:
        file_type_cat = self.get_file_type_catalog()
        for type_cat in file_type_cat:
            if type_cat.name.lower() == file_type_name.lower():
                return type_cat.id_
        return 0

    def get_picture_type_id_from_name(self, picture_type_name: str) -> int:
        picture_type_cat = self.get_picture_type_catalog()
        for pic_cat in picture_type_cat:
            if pic_cat.name.lower() == picture_type_name.lower():
                return pic_cat.id_
        return 0

    def upload_file(self, file_data: FileData, file_path: str) -> Result:
        if not file_data.file_type_id:
            if not file_data.file_type_name:
                return Result(status_code=400, message="Need either file_type_id or file_type_name for upload")
            t_file_id = self.get_file_type_id_from_name(file_data.file_type_name)
            if not t_file_id:
                return Result(status_code=400, message=f"Unknown file_type_name '{file_data.file_type_name}'")
            file_data.file_type_id = t_file_id

        if not file_data.entity_id:
            if not file_data.entity_name:
                return Result(status_code=400, message="Need either entity_id or entity_name for upload")
            t_entity_id = self.get_file_entity_id_from_name(file_data.entity_name)
            if not t_entity_id:
                return Result(status_code=400, message=f"Unknown entity_name '{file_data.entity_name}'")
            file_data.entity_id = t_entity_id

        if not file_data.entity_name:
            file_data.entity_name = self.get_file_entity_name_from_id(file_data.entity_id)

        if not file_data.data_privacy_category_id:
            file_data.data_privacy_category_id = 1

        if not os.path.exists(file_path):
            return Result(status_code=400, message=f"File '{file_path}' does not exist.")

        tcontent = file_to_base64(file_path)
        tchecksum = sha1sum(file_path)

        data_dict = {
            "Filename": file_data.file_name,
            "CreationDate": file_data.creation_date,
            "FileTypeId": file_data.file_type_id,
            "DataPrivacyCategoryId": file_data.data_privacy_category_id,
            "EntityId": file_data.entity_id,
            "Contents": tcontent,
            "Sha1Hash": tchecksum
        }

        result = self._rest_adapter.post(endpoint=f'DocumentEdit/{file_data.entity_type_name}/File', data=data_dict)
        return result

    def get_memberships(self,
                        membership_id: int = None,
                        membership_id_num: str = None,
                        person_id: int = None,
                        person_id_num: str = None,
                        active_on: str | datetime = None,
                        limit: int = None,
                        offset: int = 0,
                        add_args: Dict = None,
                        force_refresh: bool = True,
                        fetch_all: bool = False,
                        ) -> List[CooperativeMembership]:

        filter_params = {}
        if active_on:
            if isinstance(active_on, str):
                filter_params['activeOn'] = active_on
            elif isinstance(active_on, datetime):
                filter_params['activeOn'] = datetime.strftime(active_on, "%Y-%m-%d")
        if membership_id:
            filter_params['cooperativeMembershipId'] = membership_id
        if membership_id_num:
            filter_params['cooperativeMembershipIdNum'] = membership_id_num
        if person_id:
            filter_params['personId'] = person_id
        if person_id_num:
            filter_params['personIdNum'] = person_id_num

        if limit is not None:
            filter_params['limit'] = limit
        filter_params['offset'] = offset

        filter_params['showNullValues'] = 'true'

        if add_args is not None:
            filter_params.update(add_args)

        retlist = []

        if not fetch_all:
            result = self._rest_adapter.get(endpoint='CooperativeManagement/CooperativeMemberships',
                                            ep_params=filter_params,
                                            force_refresh=force_refresh)
        else:
            result = Result(0, "", [])
            merge_schema = {"mergeStrategy": "append"}
            merger = Merger(schema=merge_schema)
            filter_params['offset'] = 0
            filter_params['limit'] = 100
            response_count = 100
            while response_count == 100:
                part_result = self._rest_adapter.get(endpoint='CooperativeManagement/CooperativeMemberships',
                                                     ep_params=filter_params,
                                                     force_refresh=force_refresh)
                result.data = merger.merge(result.data, part_result.data)
                filter_params['offset'] += 100
                response_count = len(part_result.data)
                print(f"Membership-Count: {len(result.data)}")
        for entry in result.data:
            data = dict(humps.decamelize(entry))
            ret_la = CooperativeMembership(**data)
            retlist.append(ret_la)

        return retlist

    def get_facilities(self,
                       use_unit_id: int = None,
                       building_id: int = None,
                       economic_unit_id: int = None,
                       property_id: int = None,
                       limit: int = None,
                       offset: int = 0,
                       add_args: Dict = None,
                       force_refresh: bool = True,
                       fetch_all: bool = False,
                       ) -> List[FacilityElement]:

        filter_params = {}
        if use_unit_id:
            filter_params['useUnitId'] = use_unit_id
        if building_id:
            filter_params['buildingId'] = building_id
        if economic_unit_id:
            filter_params['economicUnitId'] = economic_unit_id
        if property_id:
            filter_params['propertyId'] = property_id

        if limit is not None:
            filter_params['limit'] = limit
        filter_params['offset'] = offset

        filter_params['showNullValues'] = 'true'

        if add_args is not None:
            filter_params.update(add_args)

        retlist = []

        if not fetch_all:
            result = self._rest_adapter.get(endpoint='CommercialInventory/Facility',
                                            ep_params=filter_params,
                                            force_refresh=force_refresh)
        else:
            result = Result(0, "", [])
            merge_schema = {"mergeStrategy": "append"}
            merger = Merger(schema=merge_schema)
            filter_params['offset'] = 0
            filter_params['limit'] = 100
            response_count = 100
            while response_count == 100:
                part_result = self._rest_adapter.get(endpoint='CommercialInventory/Facility',
                                                     ep_params=filter_params,
                                                     force_refresh=force_refresh)
                result.data = merger.merge(result.data, part_result.data)
                filter_params['offset'] += 100
                response_count = len(part_result.data)
                print(f"Facility-Count: {len(result.data)}")
        for entry in result.data:
            data = dict(humps.decamelize(entry))
            ret_la = FacilityElement(**data)
            retlist.append(ret_la)

        return retlist

    def get_components(self,
                       use_unit_id: int = None,
                       building_id: int = None,
                       economic_unit_id: int = None,
                       land_id: int = None,
                       limit: int = None,
                       facility_id: int = None,
                       component_id: int = None,
                       offset: int = 0,
                       add_args: Dict = None,
                       force_refresh: bool = True,
                       fetch_all: bool = False,
                       ) -> List[ComponentElement]:

        filter_params = {}
        if use_unit_id:
            filter_params['useUnitId'] = use_unit_id
        if building_id:
            filter_params['buildingId'] = building_id
        if economic_unit_id:
            filter_params['economicUnitId'] = economic_unit_id
        if land_id:
            filter_params['landId'] = land_id
        if facility_id:
            filter_params['facilityId'] = facility_id
        if component_id:
            filter_params['componentId'] = component_id

        if limit is not None:
            filter_params['limit'] = limit
        filter_params['offset'] = offset

        filter_params['showNullValues'] = 'true'

        if add_args is not None:
            filter_params.update(add_args)

        retlist = []

        if not fetch_all:
            result = self._rest_adapter.get(endpoint='CommercialInventory/Component',
                                            ep_params=filter_params,
                                            force_refresh=force_refresh)
        else:
            result = Result(0, "", [])
            merge_schema = {"mergeStrategy": "append"}
            merger = Merger(schema=merge_schema)
            filter_params['offset'] = 0
            filter_params['limit'] = 100
            response_count = 100
            while response_count == 100:
                part_result = self._rest_adapter.get(endpoint='CommercialInventory/Component',
                                                     ep_params=filter_params,
                                                     force_refresh=force_refresh)
                result.data = merger.merge(result.data, part_result.data)
                filter_params['offset'] += 100
                response_count = len(part_result.data)
                print(f"Component-Count: {len(result.data)}")
        for entry in result.data:
            data = dict(humps.decamelize(entry))
            ret_la = ComponentElement(**data)
            retlist.append(ret_la)

        return retlist

    def get_facility_catalog(self,
                             limit: int = None,
                             offset: int = 0,
                             add_args: Dict = None
                             ) -> List[FacilityCatalogElement]:

        filter_params = {}
        if limit is not None:
            filter_params['limit'] = limit
        filter_params['offset'] = offset

        filter_params['showNullValues'] = 'true'

        if add_args is not None:
            filter_params.update(add_args)

        retlist = []
        result = Result(0, "", [])
        merge_schema = {"mergeStrategy": "append"}
        merger = Merger(schema=merge_schema)
        filter_params['offset'] = 0
        filter_params['limit'] = 100
        response_count = 100
        while response_count == 100:
            part_result = self._rest_adapter.get(endpoint='CommercialInventoryCatalog/FacilityCatalog',
                                                 ep_params=filter_params,
                                                 force_refresh=True)
            result.data = merger.merge(result.data, part_result.data)
            filter_params['offset'] += 100
            response_count = len(part_result.data)
            print(f"Facility-Catalog-Count: {len(result.data)}")
        for entry in result.data:
            data = dict(humps.decamelize(entry))
            ret_la = FacilityCatalogElement(**data)
            retlist.append(ret_la)

        return retlist

    def get_component_catalog(self,
                              limit: int = None,
                              offset: int = 0,
                              add_args: Dict = None
                              ) -> List[ComponentCatalogElement]:

        filter_params = {}
        if limit is not None:
            filter_params['limit'] = limit
        filter_params['offset'] = offset

        filter_params['showNullValues'] = 'true'

        if add_args is not None:
            filter_params.update(add_args)

        retlist = []
        result = Result(0, "", [])
        merge_schema = {"mergeStrategy": "append"}
        merger = Merger(schema=merge_schema)
        filter_params['offset'] = 0
        filter_params['limit'] = 100
        response_count = 100
        while response_count == 100:
            part_result = self._rest_adapter.get(endpoint='CommercialInventoryCatalog/ComponentCatalog',
                                                 ep_params=filter_params,
                                                 force_refresh=True)
            result.data = merger.merge(result.data, part_result.data)
            filter_params['offset'] += 100
            response_count = len(part_result.data)
            print(f"Component-Catalog-Count: {len(result.data)}")
        for entry in result.data:
            data = dict(humps.decamelize(entry))
            ret_la = ComponentCatalogElement(**data)
            retlist.append(ret_la)

        return retlist

    def get_under_component_catalog(self,
                                    limit: int = None,
                                    offset: int = 0,
                                    add_args: Dict = None
                                    ) -> List[UnderComponentCatalogElement]:

        filter_params = {}
        if limit is not None:
            filter_params['limit'] = limit
        filter_params['offset'] = offset

        filter_params['showNullValues'] = 'true'

        if add_args is not None:
            filter_params.update(add_args)

        retlist = []
        result = Result(0, "", [])
        merge_schema = {"mergeStrategy": "append"}
        merger = Merger(schema=merge_schema)
        filter_params['offset'] = 0
        filter_params['limit'] = 100
        response_count = 100
        while response_count == 100:
            part_result = self._rest_adapter.get(endpoint='CommercialInventoryCatalog/UnderComponent',
                                                 ep_params=filter_params,
                                                 force_refresh=True)
            result.data = merger.merge(result.data, part_result.data)
            filter_params['offset'] += 100
            response_count = len(part_result.data)
            print(f"Under-Component-Catalog-Count: {len(result.data)}")
        for entry in result.data:
            data = dict(humps.decamelize(entry))
            ret_la = UnderComponentCatalogElement(**data)
            retlist.append(ret_la)

        return retlist

    def get_estate_picture_types(self, add_args: Dict = None) -> List[EstatePictureType]:
        filter_params = {}
        if add_args is not None:
            filter_params.update(add_args)

        retlist = []
        result = self._rest_adapter.get(endpoint='MediaReadCatalog/EstatePictureType',
                                        ep_params=filter_params,
                                        force_refresh=True)
        print(f"EstatePictureType-Count: {len(result.data)}")
        for entry in result.data:
            data = dict(humps.decamelize(entry))
            ret_la = EstatePictureType(**data)
            retlist.append(ret_la)
        return retlist

    def get_media_entities(self, add_args: Dict = None) -> List[MediaEntity]:
        filter_params = {}
        if add_args is not None:
            filter_params.update(add_args)

        retlist = []
        result = self._rest_adapter.get(endpoint='MediaReadCatalog/MediaEntity',
                                        ep_params=filter_params,
                                        force_refresh=True)
        print(f"MediaEntity-Count: {len(result.data)}")
        for entry in result.data:
            data = dict(humps.decamelize(entry))
            ret_la = MediaEntity(**data)
            retlist.append(ret_la)
        return retlist

    def create_facility(self,
                        name: str,
                        count: int,
                        facility_catalog_id: int,
                        facility_status_id: int = 3,
                        building_id: int = None,
                        economic_unit_id: int = None,
                        use_unit_id: int = None,
                        property_id: int = None,
                        inactive: bool = False):
        data_dict = {
            "Name": name,
            "Count": count,
            "FacilityCatalogId": facility_catalog_id,
            "FacilityStatusId": facility_status_id,
        }
        if building_id:
            data_dict["BuildingId"] = building_id
        if economic_unit_id:
            data_dict["EconomicUnitId"] = economic_unit_id
        if use_unit_id:
            data_dict["UseUnitId"] = use_unit_id
        if property_id:
            data_dict["PropertyId"] = property_id
        if inactive is not None:
            data_dict["Inactive"] = inactive
        result = self._rest_adapter.post(endpoint='ManageFacilityAndComponents/Facility', data=data_dict)
        return result

    def edit_facility(self,
                      facility_id: int,
                      name: str,
                      count: int,
                      facility_catalog_id: int,
                      facility_status_id: int = 3,
                      building_id: int = None,
                      economic_unit_id: int = None,
                      use_unit_id: int = None,
                      property_id: int = None,
                      inactive: bool = False):
        data_dict = {
            "Name": name,
            "Count": count,
            "FacilityCatalogId": facility_catalog_id,
            "FacilityStatusId": facility_status_id
        }
        if building_id:
            data_dict["BuildingId"] = building_id
        if economic_unit_id:
            data_dict["EconomicUnitId"] = economic_unit_id
        if use_unit_id:
            data_dict["UseUnitId"] = use_unit_id
        if property_id:
            data_dict["PropertyId"] = property_id
        if inactive is not None:
            data_dict["Inactive"] = inactive
        result = self._rest_adapter.put(endpoint=f'ManageFacilityAndComponents/Facility/{str(facility_id)}',
                                        data=data_dict)
        return result

    def create_component(self,
                         name: str,
                         count: int,
                         component_status_id: int,
                         component_catalog_id: int,
                         facility_id: int,
                         repair_relevance: bool = None,
                         lease_relevance: bool = None,
                         comment: str = None,
                         acquisition_date: str = None,
                         warranty_period: str = None,
                         warranty_end: str = None,
                         warranty_conditions: str = None,
                         position: str = None,
                         valid_from: str = None,
                         valid_to: str = None,
                         under_component_ids: list[int] = None
                         ):
        data_dict = {
            "Name": name,
            "Count": count,
            "ComponentStatusId": component_status_id,
            "ComponentCatalogId": component_catalog_id,
        }
        if repair_relevance is not None:
            data_dict["RepairRelevance"] = repair_relevance
        if lease_relevance is not None:
            data_dict["LeaseRelevance"] = lease_relevance
        if comment:
            data_dict["Comment"] = comment
        if acquisition_date is not None:
            data_dict["AcquisitionDate"] = acquisition_date
        if warranty_period is not None:
            data_dict["WarrantyPeriod"] = warranty_period
        if warranty_end is not None:
            data_dict["WarrantyEnd"] = warranty_end
        if warranty_conditions is not None:
            data_dict["WarrantyConditions"] = warranty_conditions
        if position is not None:
            data_dict["Position"] = position
        if valid_from:
            data_dict["ValidFrom"] = valid_from
        else:
            data_dict["ValidFrom"] = datetime.now().strftime("%Y-%m-%d")
        if valid_to:
            data_dict["ValidTo"] = valid_to
        if under_component_ids is not None and len(under_component_ids) > 0:
            data_dict["UnderComponentIds"] = under_component_ids
        result = self._rest_adapter.post(endpoint=f'ManageFacilityAndComponents/Facility/{str(facility_id)}/Component',
                                         data=data_dict)
        return result

    def edit_component(self,
                       component_id: int,
                       name: str,
                       count: int,
                       component_status_id: int,
                       component_catalog_id: int,
                       facility_id: int,
                       repair_relevance: bool = None,
                       lease_relevance: bool = None,
                       comment: str = None,
                       acquisition_date: str = None,
                       warranty_period: str = None,
                       warranty_end: str = None,
                       warranty_conditions: str = None,
                       position: str = None,
                       valid_from: str = None,
                       valid_to: str = None,
                       under_component_ids: list[int] = None
                       ):
        data_dict = {
            "Name": name,
            "Count": count,
            "ComponentStatusId": component_status_id,
            "ComponentCatalogId": component_catalog_id,
        }
        if repair_relevance is not None:
            data_dict["RepairRelevance"] = repair_relevance
        if lease_relevance is not None:
            data_dict["LeaseRelevance"] = lease_relevance
        if comment:
            data_dict["Comment"] = comment
        if acquisition_date is not None:
            data_dict["AcquisitionDate"] = acquisition_date
        if warranty_period is not None:
            data_dict["WarrantyPeriod"] = warranty_period
        if warranty_end is not None:
            data_dict["WarrantyEnd"] = warranty_end
        if warranty_conditions is not None:
            data_dict["WarrantyConditions"] = warranty_conditions
        if position is not None:
            data_dict["Position"] = position
        if valid_from:
            data_dict["ValidFrom"] = valid_from
        else:
            data_dict["ValidFrom"] = datetime.now().strftime("%Y-%m-%d")
        if valid_to:
            data_dict["ValidTo"] = valid_to
        if under_component_ids is not None and len(under_component_ids) > 0:
            data_dict["UnderComponentIds"] = under_component_ids
        result = self._rest_adapter.put(
            endpoint=f'ManageFacilityAndComponents/Facility/{str(facility_id)}/Component/{str(component_id)}',
            data=data_dict)
        return result

    def delete_component(self, facility_id: int, component_id: int):
        data_dict = {}
        result = self._rest_adapter.delete(
            endpoint=f'ManageFacilityAndComponents/Facility/{str(facility_id)}/Component/{str(component_id)}',
            data=data_dict)
        return result

    def upload_media(self, media_data: MediaData, file_path: str) -> Result:
        if not media_data.picture_type_id:
            if not media_data.picture_type_name:
                return Result(status_code=400, message="Need either picture_type_id or picture_type_name for upload")
            t_pic_id = self.get_picture_type_id_from_name(media_data.picture_type_name)
            if not t_pic_id:
                return Result(status_code=400, message=f"Unknown picture_type_name '{media_data.picture_type_name}'")
            media_data.picture_type_id = t_pic_id

        if not media_data.entity_id:
            if not media_data.entity_name:
                return Result(status_code=400, message="Need either entity_id or entity_name for upload")
            t_entity_id = self.get_media_entity_id_from_name(media_data.entity_name)
            if not t_entity_id:
                return Result(status_code=400, message=f"Unknown entity_name '{media_data.entity_name}'")
            media_data.entity_id = t_entity_id

        if not media_data.entity_name:
            media_data.entity_name = self.get_media_entity_name_from_id(media_data.entity_id)

        if not media_data.is_for_license_agreements:
            media_data.is_for_license_agreements = False
        if not media_data.marketing_release:
            media_data.marketing_release = False

        if not os.path.exists(file_path):
            return Result(status_code=400, message=f"File '{file_path}' does not exist.")

        tcontent = file_to_base64(file_path)
        tchecksum = sha1sum(file_path)

        data_dict = {
            "Filename": media_data.file_name,
            "CreationDate": media_data.creation_date,
            "EstatePictureTypeId": media_data.picture_type_id,
            "EntityId": media_data.entity_id,
            "MarketingRelease": media_data.marketing_release,
            "IsForLicenseAgreements": media_data.is_for_license_agreements,
            "Remark": media_data.remark,
            "Contents": tcontent,
            "Sha1Hash": tchecksum
        }

        result = self._rest_adapter.post(endpoint=f'MediaEdit/{media_data.entity_type_name}/Media', data=data_dict)
        return result

    def get_media(self, entity_name: str, entity_id: int = None, file_guid: str = None,
                  file_id: int = None,
                  media_id: int = None,
                  limit: int = None,
                  offset: int = 0,
                  add_args: Dict = None,
                  fetch_all: bool = True
                  ) -> list[MediaData]:
        filter_params = {}
        if entity_id:
            filter_params['entityId'] = entity_id
        if file_guid:
            filter_params['fileGuid'] = file_guid
        if file_id:
            filter_params['fileId'] = file_id
        if media_id:
            filter_params['mediaId'] = media_id

        if limit is not None:
            filter_params['limit'] = limit
        filter_params['offset'] = offset

        filter_params['showNullValues'] = 'true'

        if add_args is not None:
            filter_params.update(add_args)

        retlist = []

        if not fetch_all:
            result = self._rest_adapter.get(endpoint=f'MediaRead/{entity_name}/MediaData',
                                            ep_params=filter_params,
                                            force_refresh=True)
        else:
            result = Result(0, "", [])
            merge_schema = {"mergeStrategy": "append"}
            merger = Merger(schema=merge_schema)
            filter_params['offset'] = 0
            filter_params['limit'] = 100
            response_count = 100
            while response_count == 100:
                part_result = self._rest_adapter.get(endpoint=f'MediaRead/{entity_name}/MediaData',
                                                     ep_params=filter_params,
                                                     force_refresh=True)
                result.data = merger.merge(result.data, part_result.data)
                filter_params['offset'] += 100
                response_count = len(part_result.data)
                print(f"Media-Count: {len(result.data)}")
        for entry in result.data:
            data = dict(humps.decamelize(entry))
            file_name = data['file']['file_name']
            entity_type_name = data['entity_name']
            creation_date_str = data['file']['creation_date']
            file_guid = data['file']['file_guid']
            thumb_guid = data['thumbnail']['file_guid']
            thumb_name = data['thumbnail']['file_name']
            data["id_"] = data.pop("id")
            ret_la = MediaData(**data, file_name=file_name, entity_type_name=entity_type_name,
                               creation_date_str=creation_date_str, file_guid=file_guid,
                               thumb_guid=thumb_guid, thumb_name=thumb_name)
            retlist.append(ret_la)

        return retlist

    def download_media(self, entity_name: str, file_guid: str, dest_file_path: str, dest_file_name: str = None,
                       is_thumbnail: bool = False):
        if not entity_name or not file_guid or not dest_file_path:
            return Result(status_code=400, message="Need entity_name, file_guid and dest_file_path")

        if not dest_file_name:
            the_media = self.get_media(file_guid=file_guid, entity_name=entity_name)[0]
            dest_file_name = the_media.file_name

        full_path = os.path.join(dest_file_path, dest_file_name)
        if is_thumbnail:
            med_endpoint = "MediaThumbnailContent"
        else:
            med_endpoint = "MediaContent"
        result = self._rest_adapter.get(endpoint=f'MediaRead/{entity_name}/{med_endpoint}/{file_guid}')
        binary_data = base64.b64decode(result.data)
        with open(full_path, "wb") as f:
            f.write(binary_data)
        return True

    def create_communication(self,
                             person_id: int,
                             communication_type_id: int = None,
                             related_address_id: int = None,
                             content: str = None,
                             explanation: str = None,
                             ):
        data_dict = {
        }
        if communication_type_id is not None:
            data_dict["CommunicationTypeId"] = communication_type_id
        if related_address_id is not None:
            data_dict["RelatedAddressId"] = related_address_id
        if content is not None:
            data_dict["Content"] = content
        if explanation is not None:
            data_dict["Explanation"] = explanation

        result = self._rest_adapter.post(
            endpoint=f'PersonsWrite/Person/{str(person_id)}/Communications',
            data=data_dict)
        return result

    def edit_communication(self,
                           person_id: int,
                           communication_id: int,
                           communication_type_id: int = None,
                           related_address_id: int = None,
                           content: str = None,
                           explanation: str = None,
                           ):
        data_dict = {
        }
        if communication_type_id is not None:
            data_dict["CommunicationTypeId"] = communication_type_id
        if related_address_id is not None:
            data_dict["RelatedAddressId"] = related_address_id
        if content is not None:
            data_dict["Content"] = content
        if explanation is not None:
            data_dict["Explanation"] = explanation

        result = self._rest_adapter.put(
            endpoint=f'PersonsWrite/Person/{str(person_id)}/Communications/{str(communication_id)}',
            data=data_dict)
        return result

    def delete_communication(self, person_id: int, communication_id: int):
        data_dict = {}
        result = self._rest_adapter.delete(
            endpoint=f'PersonsWrite/Person/{str(person_id)}/Communications/{str(communication_id)}',
            data=data_dict)
        return result

    def delete_ticket(self, ticket_id: int):
        data_dict = {}
        result = self._rest_adapter.delete(
            endpoint=f'CommunicationEdit/Ticket/{ticket_id}',
            data=data_dict)
        return result

    def _format_openwowi_date(self, value):
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%dT%H:%M:%S")
        if isinstance(value, date):
            return value.strftime("%Y-%m-%d")
        return value

    def _add_openwowi_param(self, filter_params: Dict, param_name: str, value):
        if value is not None:
            filter_params[param_name] = self._format_openwowi_date(value)

    def _add_openwowi_data(self, data_dict: Dict, param_name: str, value):
        if value is not None:
            data_dict[param_name] = self._format_openwowi_date(value)

    def _get_openwowi_list(self,
                           endpoint: str,
                           result_class,
                           filter_params: Dict = None,
                           fetch_all: bool = False,
                           count_label: str = None,
                           force_refresh: bool = False) -> List:
        if filter_params is None:
            filter_params = {}

        retlist = []
        if not fetch_all:
            result = self._rest_adapter.get(endpoint=endpoint,
                                            ep_params=filter_params,
                                            force_refresh=force_refresh)
        else:
            result = Result(0, "", [])
            merge_schema = {"mergeStrategy": "append"}
            merger = Merger(schema=merge_schema)
            filter_params['offset'] = 0
            filter_params['limit'] = 100
            response_count = 100
            while response_count == 100:
                part_result = self._rest_adapter.get(endpoint=endpoint,
                                                     ep_params=filter_params,
                                                     force_refresh=force_refresh)
                result.data = merger.merge(result.data, part_result.data)
                filter_params['offset'] += 100
                response_count = len(part_result.data)
                if count_label is not None:
                    print(f"{count_label}-Count: {len(result.data)}")

        for entry in result.data:
            data = dict(humps.decamelize(entry))
            if "id" in data.keys():
                data["id_"] = data.pop("id")
            ret_la = result_class(**data)
            retlist.append(ret_la)

        return retlist

    def get_commissioning_craft_process_types(self,
                                              show_null_values: bool = False,
                                              add_args: Dict = None) -> List[CommissioningCraftProcessType]:
        filter_params = {}
        filter_params['showNullValues'] = 'true' if show_null_values else 'false'
        if add_args is not None:
            filter_params.update(add_args)
        return self._get_openwowi_list('CommissioningCatalog/CraftProcessTypes',
                                       CommissioningCraftProcessType,
                                       filter_params,
                                       force_refresh=True)

    def get_commissioning_commission_types(self,
                                           include_commission_control: bool = None,
                                           show_null_values: bool = False,
                                           add_args: Dict = None) -> List[CommissioningCommissionType]:
        filter_params = {}
        self._add_openwowi_param(filter_params, 'includeCommissionControl', include_commission_control)
        filter_params['showNullValues'] = 'true' if show_null_values else 'false'
        if add_args is not None:
            filter_params.update(add_args)
        return self._get_openwowi_list('CommissioningCatalog/CommissionTypes',
                                       CommissioningCommissionType,
                                       filter_params,
                                       force_refresh=True)

    def get_commissioning_craft_activities(self,
                                           show_null_values: bool = False,
                                           add_args: Dict = None) -> List[CommissioningCraftActivity]:
        filter_params = {}
        filter_params['showNullValues'] = 'true' if show_null_values else 'false'
        if add_args is not None:
            filter_params.update(add_args)
        return self._get_openwowi_list('CommissioningCatalog/CraftActivities',
                                       CommissioningCraftActivity,
                                       filter_params,
                                       force_refresh=True)

    def get_commissioning_damage_causes_catalog(self,
                                                show_null_values: bool = False,
                                                add_args: Dict = None) -> List[CommissioningDamageCause]:
        filter_params = {}
        filter_params['showNullValues'] = 'true' if show_null_values else 'false'
        if add_args is not None:
            filter_params.update(add_args)
        return self._get_openwowi_list('CommissioningCatalog/DamageCauses',
                                       CommissioningDamageCause,
                                       filter_params,
                                       force_refresh=True)

    def get_commissioning_damage_divisions_catalog(self,
                                                   show_null_values: bool = False,
                                                   add_args: Dict = None) -> List[CommissioningDamageDivision]:
        filter_params = {}
        filter_params['showNullValues'] = 'true' if show_null_values else 'false'
        if add_args is not None:
            filter_params.update(add_args)
        return self._get_openwowi_list('CommissioningCatalog/DamageDivisions',
                                       CommissioningDamageDivision,
                                       filter_params,
                                       force_refresh=True)

    def get_commissioning_notification_methods(self,
                                               show_null_values: bool = False,
                                               add_args: Dict = None) -> List[CommissioningNotificationMethod]:
        filter_params = {}
        filter_params['showNullValues'] = 'true' if show_null_values else 'false'
        if add_args is not None:
            filter_params.update(add_args)
        return self._get_openwowi_list('CommissioningCatalog/CommissionNotificationMethods',
                                       CommissioningNotificationMethod,
                                       filter_params,
                                       force_refresh=True)

    def get_commissioning_craftsmen(self,
                                    limit: int = None,
                                    offset: int = 0,
                                    company_code_id: int = None,
                                    management_id: int = None,
                                    creditor_id: int = None,
                                    creditor_number: str = None,
                                    craftsman_id: int = None,
                                    person_id: int = None,
                                    include_main_communication: bool = False,
                                    include_person_addresses: bool = False,
                                    include_person_communications: bool = False,
                                    include_person_bank_accounts: bool = False,
                                    include_craftsman_accessibility: bool = False,
                                    show_null_values: bool = False,
                                    add_args: Dict = None,
                                    fetch_all: bool = False) -> List[CommissioningCraftsman]:
        filter_params = {}
        self._add_openwowi_param(filter_params, 'limit', limit)
        self._add_openwowi_param(filter_params, 'offset', offset)
        self._add_openwowi_param(filter_params, 'companyCodeId', company_code_id)
        self._add_openwowi_param(filter_params, 'managementId', management_id)
        self._add_openwowi_param(filter_params, 'creditorId', creditor_id)
        self._add_openwowi_param(filter_params, 'creditorNumber', creditor_number)
        self._add_openwowi_param(filter_params, 'craftsmanId', craftsman_id)
        self._add_openwowi_param(filter_params, 'personId', person_id)
        filter_params['includeMainCommunication'] = 'true' if include_main_communication else 'false'
        filter_params['includePersonAddresses'] = 'true' if include_person_addresses else 'false'
        filter_params['includePersonCommunications'] = 'true' if include_person_communications else 'false'
        filter_params['includePersonBankAccounts'] = 'true' if include_person_bank_accounts else 'false'
        filter_params['includeCraftsmanAccessibility'] = 'true' if include_craftsman_accessibility else 'false'
        filter_params['showNullValues'] = 'true' if show_null_values else 'false'
        if add_args is not None:
            filter_params.update(add_args)
        return self._get_openwowi_list('CommissioningRead/Craftsman',
                                       CommissioningCraftsman,
                                       filter_params,
                                       fetch_all,
                                       'Craftsman')

    def get_commissioning_crafts_processes(self,
                                           limit: int = None,
                                           offset: int = 0,
                                           id_: int = None,
                                           id_num: str = None,
                                           company_code_id: int = None,
                                           company_code_code: str = None,
                                           economic_unit_id: int = None,
                                           building_id: int = None,
                                           land_id: int = None,
                                           use_unit_id: int = None,
                                           license_agreement_id: int = None,
                                           craftsman_id: int = None,
                                           service_package_id: int = None,
                                           crafts_process_type_id: int = None,
                                           commission_id: int = None,
                                           invoice_receipt_id: int = None,
                                           include_commission: bool = False,
                                           include_invoice_receipt: bool = False,
                                           include_additional_field: bool = False,
                                           include_insurance_data: bool = False,
                                           show_null_values: bool = False,
                                           add_args: Dict = None,
                                           fetch_all: bool = False) -> List[CommissioningCraftsProcess]:
        filter_params = {}
        self._add_openwowi_param(filter_params, 'limit', limit)
        self._add_openwowi_param(filter_params, 'offset', offset)
        self._add_openwowi_param(filter_params, 'id', id_)
        self._add_openwowi_param(filter_params, 'idNum', id_num)
        self._add_openwowi_param(filter_params, 'companyCodeId', company_code_id)
        self._add_openwowi_param(filter_params, 'companyCodeCode', company_code_code)
        self._add_openwowi_param(filter_params, 'economicUnitId', economic_unit_id)
        self._add_openwowi_param(filter_params, 'buildingId', building_id)
        self._add_openwowi_param(filter_params, 'landId', land_id)
        self._add_openwowi_param(filter_params, 'useUnitId', use_unit_id)
        self._add_openwowi_param(filter_params, 'licenseAgreementId', license_agreement_id)
        self._add_openwowi_param(filter_params, 'craftsmanId', craftsman_id)
        self._add_openwowi_param(filter_params, 'servicePackageId', service_package_id)
        self._add_openwowi_param(filter_params, 'craftsProcessTypeId', crafts_process_type_id)
        self._add_openwowi_param(filter_params, 'commissionId', commission_id)
        self._add_openwowi_param(filter_params, 'invoiceReceiptId', invoice_receipt_id)
        filter_params['includeCommission'] = 'true' if include_commission else 'false'
        filter_params['includeInvoiceReceipt'] = 'true' if include_invoice_receipt else 'false'
        filter_params['includeAdditionalField'] = 'true' if include_additional_field else 'false'
        filter_params['includeInsuranceData'] = 'true' if include_insurance_data else 'false'
        filter_params['showNullValues'] = 'true' if show_null_values else 'false'
        if add_args is not None:
            filter_params.update(add_args)
        return self._get_openwowi_list('CommissioningRead/CraftProcesses',
                                       CommissioningCraftsProcess,
                                       filter_params,
                                       fetch_all,
                                       'CraftsProcess')

    def get_commissioning_crafts_process_notes(self,
                                               limit: int = None,
                                               offset: int = 0,
                                               id_: int = None,
                                               crafts_process_id: int = None,
                                               crafts_process_id_num: str = None,
                                               company_code_id: int = None,
                                               company_code_code: str = None,
                                               show_null_values: bool = False,
                                               add_args: Dict = None,
                                               fetch_all: bool = False) -> List[CommissioningCraftsProcessNote]:
        filter_params = {}
        self._add_openwowi_param(filter_params, 'limit', limit)
        self._add_openwowi_param(filter_params, 'offset', offset)
        self._add_openwowi_param(filter_params, 'id', id_)
        self._add_openwowi_param(filter_params, 'craftsProcessId', crafts_process_id)
        self._add_openwowi_param(filter_params, 'craftsProcessIdNum', crafts_process_id_num)
        self._add_openwowi_param(filter_params, 'companyCodeId', company_code_id)
        self._add_openwowi_param(filter_params, 'companyCodeCode', company_code_code)
        filter_params['showNullValues'] = 'true' if show_null_values else 'false'
        if add_args is not None:
            filter_params.update(add_args)
        return self._get_openwowi_list('CommissioningRead/CraftProcess/Note',
                                       CommissioningCraftsProcessNote,
                                       filter_params,
                                       fetch_all,
                                       'CraftsProcessNote')

    def get_commissioning_commissions(self,
                                      limit: int = None,
                                      offset: int = 0,
                                      id_: int = None,
                                      id_num: str = None,
                                      crafts_process_id: int = None,
                                      crafts_process_id_num: str = None,
                                      craftsman_id: int = None,
                                      commission_type_id: int = None,
                                      company_code_id: int = None,
                                      company_code_code: str = None,
                                      include_commission_items: bool = True,
                                      include_also_canceled_commission_items: bool = False,
                                      include_responsible_official_repair: bool = False,
                                      include_commission_details: bool = True,
                                      include_defects: bool = False,
                                      include_additional_field: bool = False,
                                      show_null_values: bool = True,
                                      add_args: Dict = None,
                                      fetch_all: bool = False) -> List[CommissioningCommission]:
        filter_params = {}
        self._add_openwowi_param(filter_params, 'limit', limit)
        self._add_openwowi_param(filter_params, 'offset', offset)
        self._add_openwowi_param(filter_params, 'id', id_)
        self._add_openwowi_param(filter_params, 'idNum', id_num)
        self._add_openwowi_param(filter_params, 'craftsProcessId', crafts_process_id)
        self._add_openwowi_param(filter_params, 'craftsProcessIdNum', crafts_process_id_num)
        self._add_openwowi_param(filter_params, 'craftsmanId', craftsman_id)
        self._add_openwowi_param(filter_params, 'commissionTypeId', commission_type_id)
        self._add_openwowi_param(filter_params, 'companyCodeId', company_code_id)
        self._add_openwowi_param(filter_params, 'companyCodeCode', company_code_code)
        filter_params['includeCommissionItems'] = 'true' if include_commission_items else 'false'
        filter_params[
            'includeAlsoCanceledCommissionItems'] = 'true' if include_also_canceled_commission_items else 'false'
        filter_params['includeResponsibleOfficialRepair'] = 'true' if include_responsible_official_repair else 'false'
        filter_params['includeCommissionDetails'] = 'true' if include_commission_details else 'false'
        filter_params['includeDefects'] = 'true' if include_defects else 'false'
        filter_params['includeAdditionalField'] = 'true' if include_additional_field else 'false'
        filter_params['showNullValues'] = 'true' if show_null_values else 'false'
        if add_args is not None:
            filter_params.update(add_args)
        return self._get_openwowi_list('CommissioningRead/Commissions',
                                       CommissioningCommission,
                                       filter_params,
                                       fetch_all,
                                       'Commission')

    def get_commissioning_invoice_receipt_commission_items(self,
                                                           limit: int = None,
                                                           offset: int = 0,
                                                           id_: int = None,
                                                           number: str = None,
                                                           company_code_id: int = None,
                                                           company_code_code: str = None,
                                                           commission_id: int = None,
                                                           commission_id_num: str = None,
                                                           maturity_date_from=None,
                                                           maturity_date_to=None,
                                                           invoice_date_from=None,
                                                           invoice_date_to=None,
                                                           include_payment_order: bool = False,
                                                           show_null_values: bool = False,
                                                           add_args: Dict = None,
                                                           fetch_all: bool = False) -> List[
        CommissioningInvoiceReceiptCommissionItems]:
        filter_params = {}
        self._add_openwowi_param(filter_params, 'limit', limit)
        self._add_openwowi_param(filter_params, 'offset', offset)
        self._add_openwowi_param(filter_params, 'id', id_)
        self._add_openwowi_param(filter_params, 'number', number)
        self._add_openwowi_param(filter_params, 'companyCodeId', company_code_id)
        self._add_openwowi_param(filter_params, 'companyCodeCode', company_code_code)
        self._add_openwowi_param(filter_params, 'commissionId', commission_id)
        self._add_openwowi_param(filter_params, 'commissionIdNum', commission_id_num)
        self._add_openwowi_param(filter_params, 'maturityDateFrom', maturity_date_from)
        self._add_openwowi_param(filter_params, 'maturityDateTo', maturity_date_to)
        self._add_openwowi_param(filter_params, 'invoiceDateFrom', invoice_date_from)
        self._add_openwowi_param(filter_params, 'invoiceDateTo', invoice_date_to)
        filter_params['includePaymentOrder'] = 'true' if include_payment_order else 'false'
        filter_params['showNullValues'] = 'true' if show_null_values else 'false'
        if add_args is not None:
            filter_params.update(add_args)
        return self._get_openwowi_list('CommissioningRead/InvoiceReceipt/CommissionItems',
                                       CommissioningInvoiceReceiptCommissionItems,
                                       filter_params,
                                       fetch_all,
                                       'InvoiceReceiptCommissionItems')

    def get_commissioning_invoice_receipt_payment_orders(self,
                                                         limit: int = None,
                                                         offset: int = 0,
                                                         id_: int = None,
                                                         number: str = None,
                                                         company_code_id: int = None,
                                                         company_code_code: str = None,
                                                         commission_id: int = None,
                                                         commission_id_num: str = None,
                                                         maturity_date_from=None,
                                                         maturity_date_to=None,
                                                         invoice_date_from=None,
                                                         invoice_date_to=None,
                                                         show_null_values: bool = False,
                                                         add_args: Dict = None,
                                                         fetch_all: bool = False) -> List[
        CommissioningInvoiceReceiptPaymentOrders]:
        filter_params = {}
        self._add_openwowi_param(filter_params, 'limit', limit)
        self._add_openwowi_param(filter_params, 'offset', offset)
        self._add_openwowi_param(filter_params, 'id', id_)
        self._add_openwowi_param(filter_params, 'number', number)
        self._add_openwowi_param(filter_params, 'companyCodeId', company_code_id)
        self._add_openwowi_param(filter_params, 'companyCodeCode', company_code_code)
        self._add_openwowi_param(filter_params, 'commissionId', commission_id)
        self._add_openwowi_param(filter_params, 'commissionIdNum', commission_id_num)
        self._add_openwowi_param(filter_params, 'maturityDateFrom', maturity_date_from)
        self._add_openwowi_param(filter_params, 'maturityDateTo', maturity_date_to)
        self._add_openwowi_param(filter_params, 'invoiceDateFrom', invoice_date_from)
        self._add_openwowi_param(filter_params, 'invoiceDateTo', invoice_date_to)
        filter_params['showNullValues'] = 'true' if show_null_values else 'false'
        if add_args is not None:
            filter_params.update(add_args)
        return self._get_openwowi_list('CommissioningRead/InvoiceReceipt/PaymentOrders',
                                       CommissioningInvoiceReceiptPaymentOrders,
                                       filter_params,
                                       fetch_all,
                                       'InvoiceReceiptPaymentOrders')

    def get_commissioning_service_catalogues(self,
                                             limit: int = None,
                                             offset: int = 0,
                                             id_: int = None,
                                             id_num: str = None,
                                             owner_id: int = None,
                                             owner_number: str = None,
                                             management_id: int = None,
                                             management_id_num: str = None,
                                             component_catalog_id: int = None,
                                             facility_catalog_id: int = None,
                                             include_invalid: bool = False,
                                             include_craftsman_agreements: bool = False,
                                             include_commission_types: bool = False,
                                             show_null_values: bool = False,
                                             add_args: Dict = None,
                                             fetch_all: bool = False) -> List[CommissioningServiceCatalogue]:
        filter_params = {}
        self._add_openwowi_param(filter_params, 'limit', limit)
        self._add_openwowi_param(filter_params, 'offset', offset)
        self._add_openwowi_param(filter_params, 'id', id_)
        self._add_openwowi_param(filter_params, 'idNum', id_num)
        self._add_openwowi_param(filter_params, 'ownerId', owner_id)
        self._add_openwowi_param(filter_params, 'ownerNumber', owner_number)
        self._add_openwowi_param(filter_params, 'managementId', management_id)
        self._add_openwowi_param(filter_params, 'managementIdNum', management_id_num)
        self._add_openwowi_param(filter_params, 'componentCatalogId', component_catalog_id)
        self._add_openwowi_param(filter_params, 'facilityCatalogId', facility_catalog_id)
        filter_params['includeInvalid'] = 'true' if include_invalid else 'false'
        filter_params['includeCraftsmanAgreements'] = 'true' if include_craftsman_agreements else 'false'
        filter_params['includeCommissionTypes'] = 'true' if include_commission_types else 'false'
        filter_params['showNullValues'] = 'true' if show_null_values else 'false'
        if add_args is not None:
            filter_params.update(add_args)
        return self._get_openwowi_list('CommissioningRead/ServiceCatalogue',
                                       CommissioningServiceCatalogue,
                                       filter_params,
                                       fetch_all,
                                       'ServiceCatalogue')

    def get_commissioning_service_catalogues_for_craftsman(self,
                                                           craftsman_id: int,
                                                           limit: int = None,
                                                           offset: int = 0,
                                                           id_: int = None,
                                                           id_num: str = None,
                                                           owner_id: int = None,
                                                           owner_number: str = None,
                                                           management_id: int = None,
                                                           management_id_num: str = None,
                                                           component_catalog_id: int = None,
                                                           facility_catalog_id: int = None,
                                                           include_invalid: bool = False,
                                                           include_commission_types: bool = False,
                                                           show_null_values: bool = False,
                                                           add_args: Dict = None,
                                                           fetch_all: bool = False) -> List[
        CommissioningServiceCatalogue]:
        filter_params = {}
        self._add_openwowi_param(filter_params, 'limit', limit)
        self._add_openwowi_param(filter_params, 'offset', offset)
        self._add_openwowi_param(filter_params, 'id', id_)
        self._add_openwowi_param(filter_params, 'idNum', id_num)
        self._add_openwowi_param(filter_params, 'ownerId', owner_id)
        self._add_openwowi_param(filter_params, 'ownerNumber', owner_number)
        self._add_openwowi_param(filter_params, 'managementId', management_id)
        self._add_openwowi_param(filter_params, 'managementIdNum', management_id_num)
        self._add_openwowi_param(filter_params, 'componentCatalogId', component_catalog_id)
        self._add_openwowi_param(filter_params, 'facilityCatalogId', facility_catalog_id)
        filter_params['includeInvalid'] = 'true' if include_invalid else 'false'
        filter_params['includeCommissionTypes'] = 'true' if include_commission_types else 'false'
        filter_params['showNullValues'] = 'true' if show_null_values else 'false'
        if add_args is not None:
            filter_params.update(add_args)
        return self._get_openwowi_list(f'CommissioningRead/Craftsman/{craftsman_id}/ServiceCatalogue',
                                       CommissioningServiceCatalogue,
                                       filter_params,
                                       fetch_all,
                                       'CraftsmanServiceCatalogue')

    def get_commissioning_service_packages(self,
                                           limit: int = None,
                                           offset: int = 0,
                                           id_: int = None,
                                           id_num: str = None,
                                           owner_id: int = None,
                                           owner_number: str = None,
                                           management_id: int = None,
                                           management_id_num: str = None,
                                           include_craftsman: bool = False,
                                           include_service_catalogues: bool = False,
                                           show_null_values: bool = False,
                                           add_args: Dict = None,
                                           fetch_all: bool = False) -> List[CommissioningServicePackage]:
        filter_params = {}
        self._add_openwowi_param(filter_params, 'limit', limit)
        self._add_openwowi_param(filter_params, 'offset', offset)
        self._add_openwowi_param(filter_params, 'id', id_)
        self._add_openwowi_param(filter_params, 'idNum', id_num)
        self._add_openwowi_param(filter_params, 'ownerId', owner_id)
        self._add_openwowi_param(filter_params, 'ownerNumber', owner_number)
        self._add_openwowi_param(filter_params, 'managementId', management_id)
        self._add_openwowi_param(filter_params, 'managementIdNum', management_id_num)
        filter_params['includeCraftsman'] = 'true' if include_craftsman else 'false'
        filter_params['includeServiceCatalogues'] = 'true' if include_service_catalogues else 'false'
        filter_params['showNullValues'] = 'true' if show_null_values else 'false'
        if add_args is not None:
            filter_params.update(add_args)
        return self._get_openwowi_list('CommissioningRead/ServicePackage',
                                       CommissioningServicePackage,
                                       filter_params,
                                       fetch_all,
                                       'ServicePackage')

    def get_commissioning_insurers(self,
                                   limit: int = None,
                                   offset: int = 0,
                                   company_code_id: int = None,
                                   management_id: int = None,
                                   creditor_id: int = None,
                                   creditor_number: str = None,
                                   insurer_id: int = None,
                                   person_id: int = None,
                                   include_main_communication: bool = False,
                                   include_person_addresses: bool = False,
                                   include_person_communications: bool = False,
                                   include_person_bank_accounts: bool = False,
                                   include_insurer_accessibility: bool = False,
                                   show_null_values: bool = False,
                                   add_args: Dict = None,
                                   fetch_all: bool = False) -> List[CommissioningInsurer]:
        filter_params = {}
        self._add_openwowi_param(filter_params, 'limit', limit)
        self._add_openwowi_param(filter_params, 'offset', offset)
        self._add_openwowi_param(filter_params, 'companyCodeId', company_code_id)
        self._add_openwowi_param(filter_params, 'managementId', management_id)
        self._add_openwowi_param(filter_params, 'creditorId', creditor_id)
        self._add_openwowi_param(filter_params, 'creditorNumber', creditor_number)
        self._add_openwowi_param(filter_params, 'insurerId', insurer_id)
        self._add_openwowi_param(filter_params, 'personId', person_id)
        filter_params['includeMainCommunication'] = 'true' if include_main_communication else 'false'
        filter_params['includePersonAddresses'] = 'true' if include_person_addresses else 'false'
        filter_params['includePersonCommunications'] = 'true' if include_person_communications else 'false'
        filter_params['includePersonBankAccounts'] = 'true' if include_person_bank_accounts else 'false'
        filter_params['includeInsurerAccessibility'] = 'true' if include_insurer_accessibility else 'false'
        filter_params['showNullValues'] = 'true' if show_null_values else 'false'
        if add_args is not None:
            filter_params.update(add_args)
        return self._get_openwowi_list('CommissioningRead/Insurer',
                                       CommissioningInsurer,
                                       filter_params,
                                       fetch_all,
                                       'Insurer')

    def get_commissioning_insurance_contracts(self,
                                              limit: int = None,
                                              offset: int = 0,
                                              id_: int = None,
                                              id_num: str = None,
                                              insurer_id: int = None,
                                              economic_unit_id: int = None,
                                              valid_from=None,
                                              valid_to=None,
                                              show_null_values: bool = False,
                                              add_args: Dict = None,
                                              fetch_all: bool = False) -> List[CommissioningInsuranceContract]:
        filter_params = {}
        self._add_openwowi_param(filter_params, 'limit', limit)
        self._add_openwowi_param(filter_params, 'offset', offset)
        self._add_openwowi_param(filter_params, 'id', id_)
        self._add_openwowi_param(filter_params, 'idNum', id_num)
        self._add_openwowi_param(filter_params, 'insurerId', insurer_id)
        self._add_openwowi_param(filter_params, 'economicUnitId', economic_unit_id)
        self._add_openwowi_param(filter_params, 'validFrom', valid_from)
        self._add_openwowi_param(filter_params, 'validTo', valid_to)
        filter_params['showNullValues'] = 'true' if show_null_values else 'false'
        if add_args is not None:
            filter_params.update(add_args)
        return self._get_openwowi_list('CommissioningRead/InsuranceContract',
                                       CommissioningInsuranceContract,
                                       filter_params,
                                       fetch_all,
                                       'InsuranceContract')

    def get_commissioning_invoice_receipt_flow_commission_items(self,
                                                                limit: int = None,
                                                                offset: int = 0,
                                                                id_: int = None,
                                                                number: str = None,
                                                                company_code_id: int = None,
                                                                company_code_code: str = None,
                                                                commission_id: int = None,
                                                                commission_id_num: str = None,
                                                                maturity_date_from=None,
                                                                maturity_date_to=None,
                                                                invoice_date_from=None,
                                                                invoice_date_to=None,
                                                                include_payment_order: bool = False,
                                                                show_null_values: bool = False,
                                                                add_args: Dict = None,
                                                                fetch_all: bool = False) -> List[
        CommissioningInvoiceReceiptCommissionItems]:
        filter_params = {}
        self._add_openwowi_param(filter_params, 'limit', limit)
        self._add_openwowi_param(filter_params, 'offset', offset)
        self._add_openwowi_param(filter_params, 'id', id_)
        self._add_openwowi_param(filter_params, 'number', number)
        self._add_openwowi_param(filter_params, 'companyCodeId', company_code_id)
        self._add_openwowi_param(filter_params, 'companyCodeCode', company_code_code)
        self._add_openwowi_param(filter_params, 'commissionId', commission_id)
        self._add_openwowi_param(filter_params, 'commissionIdNum', commission_id_num)
        self._add_openwowi_param(filter_params, 'maturityDateFrom', maturity_date_from)
        self._add_openwowi_param(filter_params, 'maturityDateTo', maturity_date_to)
        self._add_openwowi_param(filter_params, 'invoiceDateFrom', invoice_date_from)
        self._add_openwowi_param(filter_params, 'invoiceDateTo', invoice_date_to)
        filter_params['includePaymentOrder'] = 'true' if include_payment_order else 'false'
        filter_params['showNullValues'] = 'true' if show_null_values else 'false'
        if add_args is not None:
            filter_params.update(add_args)
        return self._get_openwowi_list('CommissioningRead/InvoiceReceiptNew/CommissionItems',
                                       CommissioningInvoiceReceiptCommissionItems,
                                       filter_params,
                                       fetch_all,
                                       'InvoiceReceiptFlowCommissionItems')

    def create_commissioning_crafts_process(self,
                                            short_description_crafts_process: str = None,
                                            crafts_process_type_id: int = None,
                                            company_code_id: int = None,
                                            crafts_process_status_id: int = None,
                                            service_package_id: int = None,
                                            project_id: int = None,
                                            management_id: int = None,
                                            owner_id: int = None,
                                            economic_unit_id: int = None,
                                            building_id: int = None,
                                            land_id: int = None,
                                            use_unit_id: int = None,
                                            license_agreement_id: int = None,
                                            person_in_charge_responsible_official_id: int = None,
                                            crafts_process_from=None,
                                            crafts_process_to=None,
                                            insurance_data: Dict = None,
                                            id_num: str = None,
                                            description: str = None,
                                            add_args: Dict = None):
        data_dict = {}
        self._add_openwowi_data(data_dict, 'ShortDescriptionCraftsProcess', short_description_crafts_process)
        self._add_openwowi_data(data_dict, 'CraftsProcessTypeId', crafts_process_type_id)
        self._add_openwowi_data(data_dict, 'CompanyCodeId', company_code_id)
        self._add_openwowi_data(data_dict, 'CraftsProcessStatusId', crafts_process_status_id)
        self._add_openwowi_data(data_dict, 'ServicePackageId', service_package_id)
        self._add_openwowi_data(data_dict, 'ProjectId', project_id)
        self._add_openwowi_data(data_dict, 'ManagementId', management_id)
        self._add_openwowi_data(data_dict, 'OwnerId', owner_id)
        self._add_openwowi_data(data_dict, 'EconomicUnitId', economic_unit_id)
        self._add_openwowi_data(data_dict, 'BuildingId', building_id)
        self._add_openwowi_data(data_dict, 'LandId', land_id)
        self._add_openwowi_data(data_dict, 'UseUnitId', use_unit_id)
        self._add_openwowi_data(data_dict, 'LicenseAgreementId', license_agreement_id)
        self._add_openwowi_data(data_dict, 'PersonInChargeResponsibleOfficialId',
                                person_in_charge_responsible_official_id)
        self._add_openwowi_data(data_dict, 'CraftsProcessFrom', crafts_process_from)
        self._add_openwowi_data(data_dict, 'CraftsProcessTo', crafts_process_to)
        self._add_openwowi_data(data_dict, 'InsuranceData', insurance_data)
        self._add_openwowi_data(data_dict, 'IdNum', id_num)
        self._add_openwowi_data(data_dict, 'Description', description)
        if add_args is not None:
            data_dict.update(add_args)
        return self._rest_adapter.post(endpoint='CommissioningEdit/CraftsProcess', data=data_dict)

    def edit_commissioning_crafts_process(self,
                                          crafts_process_id: int,
                                          short_description_crafts_process: str = None,
                                          crafts_process_type_id: int = None,
                                          company_code_id: int = None,
                                          crafts_process_status_id: int = None,
                                          service_package_id: int = None,
                                          project_id: int = None,
                                          management_id: int = None,
                                          owner_id: int = None,
                                          economic_unit_id: int = None,
                                          building_id: int = None,
                                          land_id: int = None,
                                          use_unit_id: int = None,
                                          license_agreement_id: int = None,
                                          person_in_charge_responsible_official_id: int = None,
                                          crafts_process_from=None,
                                          crafts_process_to=None,
                                          insurance_data: Dict = None,
                                          add_args: Dict = None):
        data_dict = {}
        self._add_openwowi_data(data_dict, 'ShortDescriptionCraftsProcess', short_description_crafts_process)
        self._add_openwowi_data(data_dict, 'CraftsProcessTypeId', crafts_process_type_id)
        self._add_openwowi_data(data_dict, 'CompanyCodeId', company_code_id)
        self._add_openwowi_data(data_dict, 'CraftsProcessStatusId', crafts_process_status_id)
        self._add_openwowi_data(data_dict, 'ServicePackageId', service_package_id)
        self._add_openwowi_data(data_dict, 'ProjectId', project_id)
        self._add_openwowi_data(data_dict, 'ManagementId', management_id)
        self._add_openwowi_data(data_dict, 'OwnerId', owner_id)
        self._add_openwowi_data(data_dict, 'EconomicUnitId', economic_unit_id)
        self._add_openwowi_data(data_dict, 'BuildingId', building_id)
        self._add_openwowi_data(data_dict, 'LandId', land_id)
        self._add_openwowi_data(data_dict, 'UseUnitId', use_unit_id)
        self._add_openwowi_data(data_dict, 'LicenseAgreementId', license_agreement_id)
        self._add_openwowi_data(data_dict, 'PersonInChargeResponsibleOfficialId',
                                person_in_charge_responsible_official_id)
        self._add_openwowi_data(data_dict, 'CraftsProcessFrom', crafts_process_from)
        self._add_openwowi_data(data_dict, 'CraftsProcessTo', crafts_process_to)
        self._add_openwowi_data(data_dict, 'InsuranceData', insurance_data)
        if add_args is not None:
            data_dict.update(add_args)
        return self._rest_adapter.put(endpoint=f'CommissioningEdit/CraftsProcess/{crafts_process_id}', data=data_dict)

    def delete_commissioning_crafts_process(self, crafts_process_id: int):
        data_dict = {}
        return self._rest_adapter.delete(endpoint=f'CommissioningEdit/CraftsProcess/{crafts_process_id}',
                                         data=data_dict)

    def create_commissioning_commission(self,
                                        crafts_process_id: int = None,
                                        id_num: str = None,
                                        code: str = None,
                                        external_identification_number: str = None,
                                        commission_type_id: int = None,
                                        creditor_id: int = None,
                                        use_unit_id: int = None,
                                        building_id: int = None,
                                        land_id: int = None,
                                        economic_unit_id: int = None,
                                        license_agreement_id: int = None,
                                        property_management_contract_id: int = None,
                                        responsible_official_repair_id: int = None,
                                        department_id: int = None,
                                        recording_date=None,
                                        completion_date=None,
                                        placing_date=None,
                                        acceptance_date=None,
                                        execution_from=None,
                                        execution_to=None,
                                        time_damage=None,
                                        positions: List[Dict] = None,
                                        facility_id: int = None,
                                        component_id: int = None,
                                        commission_status_id: int = None,
                                        short_description_crafts_process: str = None,
                                        add_args: Dict = None):
        data_dict = {}
        self._add_openwowi_data(data_dict, 'CraftsProcessId', crafts_process_id)
        self._add_openwowi_data(data_dict, 'IdNum', id_num)
        self._add_openwowi_data(data_dict, 'Code', code)
        self._add_openwowi_data(data_dict, 'ExternalIdentificationNumber', external_identification_number)
        self._add_openwowi_data(data_dict, 'CommissionTypeId', commission_type_id)
        self._add_openwowi_data(data_dict, 'CreditorId', creditor_id)
        self._add_openwowi_data(data_dict, 'UseUnitId', use_unit_id)
        self._add_openwowi_data(data_dict, 'BuildingId', building_id)
        self._add_openwowi_data(data_dict, 'LandId', land_id)
        self._add_openwowi_data(data_dict, 'EconomicUnitId', economic_unit_id)
        self._add_openwowi_data(data_dict, 'LicenseAgreementId', license_agreement_id)
        self._add_openwowi_data(data_dict, 'PropertyManagementContractId', property_management_contract_id)
        self._add_openwowi_data(data_dict, 'ResponsibleOfficialRepairId', responsible_official_repair_id)
        self._add_openwowi_data(data_dict, 'DepartmentId', department_id)
        self._add_openwowi_data(data_dict, 'RecordingDate', recording_date)
        self._add_openwowi_data(data_dict, 'CompletionDate', completion_date)
        self._add_openwowi_data(data_dict, 'PlacingDate', placing_date)
        self._add_openwowi_data(data_dict, 'AcceptanceDate', acceptance_date)
        self._add_openwowi_data(data_dict, 'ExecutionFrom', execution_from)
        self._add_openwowi_data(data_dict, 'ExecutionTo', execution_to)
        self._add_openwowi_data(data_dict, 'TimeDamage', time_damage)
        self._add_openwowi_data(data_dict, 'Positions', positions)
        self._add_openwowi_data(data_dict, 'FacilityId', facility_id)
        self._add_openwowi_data(data_dict, 'ComponentId', component_id)
        self._add_openwowi_data(data_dict, 'CommissionStatusId', commission_status_id)
        self._add_openwowi_data(data_dict, 'ShortDescriptionCraftsProcess', short_description_crafts_process)
        if add_args is not None:
            data_dict.update(add_args)
        return self._rest_adapter.post(endpoint='CommissioningEdit/Commission', data=data_dict)

    def create_commissioning_commission_wait_for_craftsman_feedback(self,
                                                                    crafts_process_id: int = None,
                                                                    id_num: str = None,
                                                                    code: str = None,
                                                                    external_identification_number: str = None,
                                                                    commission_type_id: int = None,
                                                                    creditor_id: int = None,
                                                                    use_unit_id: int = None,
                                                                    building_id: int = None,
                                                                    land_id: int = None,
                                                                    economic_unit_id: int = None,
                                                                    license_agreement_id: int = None,
                                                                    property_management_contract_id: int = None,
                                                                    responsible_official_repair_id: int = None,
                                                                    department_id: int = None,
                                                                    recording_date=None,
                                                                    completion_date=None,
                                                                    placing_date=None,
                                                                    acceptance_date=None,
                                                                    execution_from=None,
                                                                    execution_to=None,
                                                                    time_damage=None,
                                                                    positions: List[Dict] = None,
                                                                    facility_id: int = None,
                                                                    component_id: int = None,
                                                                    short_description_crafts_process: str = None,
                                                                    add_args: Dict = None):
        data_dict = {}
        self._add_openwowi_data(data_dict, 'CraftsProcessId', crafts_process_id)
        self._add_openwowi_data(data_dict, 'IdNum', id_num)
        self._add_openwowi_data(data_dict, 'Code', code)
        self._add_openwowi_data(data_dict, 'ExternalIdentificationNumber', external_identification_number)
        self._add_openwowi_data(data_dict, 'CommissionTypeId', commission_type_id)
        self._add_openwowi_data(data_dict, 'CreditorId', creditor_id)
        self._add_openwowi_data(data_dict, 'UseUnitId', use_unit_id)
        self._add_openwowi_data(data_dict, 'BuildingId', building_id)
        self._add_openwowi_data(data_dict, 'LandId', land_id)
        self._add_openwowi_data(data_dict, 'EconomicUnitId', economic_unit_id)
        self._add_openwowi_data(data_dict, 'LicenseAgreementId', license_agreement_id)
        self._add_openwowi_data(data_dict, 'PropertyManagementContractId', property_management_contract_id)
        self._add_openwowi_data(data_dict, 'ResponsibleOfficialRepairId', responsible_official_repair_id)
        self._add_openwowi_data(data_dict, 'DepartmentId', department_id)
        self._add_openwowi_data(data_dict, 'RecordingDate', recording_date)
        self._add_openwowi_data(data_dict, 'CompletionDate', completion_date)
        self._add_openwowi_data(data_dict, 'PlacingDate', placing_date)
        self._add_openwowi_data(data_dict, 'AcceptanceDate', acceptance_date)
        self._add_openwowi_data(data_dict, 'ExecutionFrom', execution_from)
        self._add_openwowi_data(data_dict, 'ExecutionTo', execution_to)
        self._add_openwowi_data(data_dict, 'TimeDamage', time_damage)
        self._add_openwowi_data(data_dict, 'Positions', positions)
        self._add_openwowi_data(data_dict, 'FacilityId', facility_id)
        self._add_openwowi_data(data_dict, 'ComponentId', component_id)
        self._add_openwowi_data(data_dict, 'ShortDescriptionCraftsProcess', short_description_crafts_process)
        if add_args is not None:
            data_dict.update(add_args)
        return self._rest_adapter.post(endpoint='CommissioningEdit/Commission/WaitForCraftsmanFeedback', data=data_dict)

    def set_commissioning_commission_to_accepted(self, commission_id: int):
        data_dict = {}
        return self._rest_adapter.put(endpoint=f'CommissioningEdit/Commission/{commission_id}/Accepted', data=data_dict)

    def set_commissioning_commission_to_refused(self, commission_id: int, reason_for_refusal: str = None):
        data_dict = {}
        self._add_openwowi_data(data_dict, 'ReasonForRefusal', reason_for_refusal)
        return self._rest_adapter.put(endpoint=f'CommissioningEdit/Commission/{commission_id}/Refused', data=data_dict)

    def set_commissioning_commission_to_await_invoice(self, commission_id: int):
        data_dict = {}
        return self._rest_adapter.put(endpoint=f'CommissioningEdit/Commission/{commission_id}/AwaitInvoice',
                                      data=data_dict)

    def set_commissioning_commission_to_done(self, commission_id: int):
        data_dict = {}
        return self._rest_adapter.put(endpoint=f'CommissioningEdit/Commission/{commission_id}/Done', data=data_dict)

    def set_commissioning_commission_to_imported(self, commission_id: int):
        data_dict = {}
        return self._rest_adapter.put(endpoint=f'CommissioningEdit/Commission/{commission_id}/Imported', data=data_dict)

    def set_commissioning_commission_to_canceled(self, commission_id: int):
        data_dict = {}
        return self._rest_adapter.put(endpoint=f'CommissioningEdit/Commission/{commission_id}/Canceled', data=data_dict)

    def set_commissioning_craftsman_crafts_portal_id(self, craftsman_id: int, craftsman_portal_id: str = None):
        data_dict = {}
        self._add_openwowi_data(data_dict, 'CraftsmanPortalId', craftsman_portal_id)
        return self._rest_adapter.put(endpoint=f'CommissioningEdit/Craftsman/{craftsman_id}', data=data_dict)

    def create_commissioning_crafts_process_note(self, crafts_process_id: int, description: str):
        return self._rest_adapter.post(endpoint=f'CommissioningEdit/CraftsProcess/{crafts_process_id}/Note',
                                       data=description)

    def edit_commissioning_crafts_process_note(self, crafts_process_id: int, note_id: int, description: str):
        return self._rest_adapter.put(endpoint=f'CommissioningEdit/CraftsProcess/{crafts_process_id}/Note/{note_id}',
                                      data=description)

    def delete_commissioning_crafts_process_note(self, crafts_process_id: int, note_id: int):
        data_dict = {}
        return self._rest_adapter.delete(endpoint=f'CommissioningEdit/CraftsProcess/{crafts_process_id}/Note/{note_id}',
                                         data=data_dict)

    def create_commissioning_insurance_contract(self,
                                                id_num: str = None,
                                                node_id: int = None,
                                                code: str = None,
                                                insurer_id: int = None,
                                                valid_from=None,
                                                valid_to=None,
                                                assigned_commissioning_insurance_damage_divisions: List[Dict] = None,
                                                assigned_economic_units: List[Dict] = None,
                                                add_args: Dict = None):
        data_dict = {}
        self._add_openwowi_data(data_dict, 'IdNum', id_num)
        self._add_openwowi_data(data_dict, 'NodeId', node_id)
        self._add_openwowi_data(data_dict, 'Code', code)
        self._add_openwowi_data(data_dict, 'InsurerId', insurer_id)
        self._add_openwowi_data(data_dict, 'ValidFrom', valid_from)
        self._add_openwowi_data(data_dict, 'ValidTo', valid_to)
        self._add_openwowi_data(data_dict, 'AssignedCommissioningInsuranceDamageDivisions',
                                assigned_commissioning_insurance_damage_divisions)
        self._add_openwowi_data(data_dict, 'AssignedEconomicUnits', assigned_economic_units)
        if add_args is not None:
            data_dict.update(add_args)
        return self._rest_adapter.post(endpoint='CommissioningEdit/InsuranceContract', data=data_dict)

    def edit_commissioning_insurance_contract(self,
                                              insurance_contract_id: int,
                                              id_num: str = None,
                                              code: str = None,
                                              insurer_id: int = None,
                                              valid_from=None,
                                              valid_to=None,
                                              assigned_commissioning_insurance_damage_divisions: List[Dict] = None,
                                              assigned_economic_units: List[Dict] = None,
                                              add_args: Dict = None):
        data_dict = {}
        self._add_openwowi_data(data_dict, 'IdNum', id_num)
        self._add_openwowi_data(data_dict, 'Code', code)
        self._add_openwowi_data(data_dict, 'InsurerId', insurer_id)
        self._add_openwowi_data(data_dict, 'ValidFrom', valid_from)
        self._add_openwowi_data(data_dict, 'ValidTo', valid_to)
        self._add_openwowi_data(data_dict, 'AssignedCommissioningInsuranceDamageDivisions',
                                assigned_commissioning_insurance_damage_divisions)
        self._add_openwowi_data(data_dict, 'AssignedEconomicUnits', assigned_economic_units)
        if add_args is not None:
            data_dict.update(add_args)
        return self._rest_adapter.put(endpoint=f'CommissioningEdit/InsuranceContract/{insurance_contract_id}',
                                      data=data_dict)

    def create_commissioning_damage_division(self,
                                             id_num: str = None,
                                             code: str = None,
                                             external_identification_number: str = None,
                                             node_id: int = None,
                                             add_args: Dict = None):
        data_dict = {}
        self._add_openwowi_data(data_dict, 'IdNum', id_num)
        self._add_openwowi_data(data_dict, 'Code', code)
        self._add_openwowi_data(data_dict, 'ExternalIdentificationNumber', external_identification_number)
        self._add_openwowi_data(data_dict, 'NodeId', node_id)
        if add_args is not None:
            data_dict.update(add_args)
        return self._rest_adapter.post(endpoint='CommissioningEdit/DamageDivision', data=data_dict)

    def edit_commissioning_damage_division(self,
                                           damage_division_id: int,
                                           id_num: str = None,
                                           code: str = None,
                                           external_identification_number: str = None,
                                           node_id: int = None,
                                           add_args: Dict = None):
        data_dict = {}
        self._add_openwowi_data(data_dict, 'IdNum', id_num)
        self._add_openwowi_data(data_dict, 'Code', code)
        self._add_openwowi_data(data_dict, 'ExternalIdentificationNumber', external_identification_number)
        self._add_openwowi_data(data_dict, 'NodeId', node_id)
        if add_args is not None:
            data_dict.update(add_args)
        return self._rest_adapter.put(endpoint=f'CommissioningEdit/DamageDivision/{damage_division_id}',
                                      data=data_dict)

    def delete_commissioning_damage_division(self, damage_division_id: int):
        data_dict = {}
        return self._rest_adapter.delete(endpoint=f'CommissioningEdit/DamageDivision/{damage_division_id}',
                                         data=data_dict)

    def create_commissioning_damage_cause(self,
                                          id_num: str = None,
                                          damage_division_id: int = None,
                                          external_identification_number: str = None,
                                          code: str = None,
                                          add_args: Dict = None):
        data_dict = {}
        self._add_openwowi_data(data_dict, 'IdNum', id_num)
        self._add_openwowi_data(data_dict, 'DamageDivisionId', damage_division_id)
        self._add_openwowi_data(data_dict, 'ExternalIdentificationNumber', external_identification_number)
        self._add_openwowi_data(data_dict, 'Code', code)
        if add_args is not None:
            data_dict.update(add_args)
        return self._rest_adapter.post(endpoint='CommissioningEdit/DamageCause', data=data_dict)

    def edit_commissioning_damage_cause(self,
                                        damage_cause_id: int,
                                        id_num: str = None,
                                        damage_division_id: int = None,
                                        external_identification_number: str = None,
                                        code: str = None,
                                        add_args: Dict = None):
        data_dict = {}
        self._add_openwowi_data(data_dict, 'IdNum', id_num)
        self._add_openwowi_data(data_dict, 'DamageDivisionId', damage_division_id)
        self._add_openwowi_data(data_dict, 'ExternalIdentificationNumber', external_identification_number)
        self._add_openwowi_data(data_dict, 'Code', code)
        if add_args is not None:
            data_dict.update(add_args)
        return self._rest_adapter.put(endpoint=f'CommissioningEdit/DamageCause/{damage_cause_id}',
                                      data=data_dict)
