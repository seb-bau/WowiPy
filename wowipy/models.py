from typing import List, Dict, Optional
from datetime import datetime


class Result:
    def __init__(self, status_code: int, message: str = '', data: List[Dict] = None):
        self.status_code = int(status_code)
        self.message = str(message)
        self.data = data if data else []


class IdNameCombination:
    id_: int
    name: str

    def __init__(self, name: str, id_: int = None, **kwargs) -> None:
        if id_ is not None:
            self.id_ = id_
        else:
            self.id_ = kwargs.get('id')
        self.name = name


class DebitEntryType(IdNameCombination):
    pass


class StatusContract(IdNameCombination):
    pass


class LifeOfContract(IdNameCombination):
    pass


class PaymentInterval(IdNameCombination):
    pass


class PeriodOfNotice(IdNameCombination):
    pass


class AdministrationType(IdNameCombination):
    pass


class CommunicationType(IdNameCombination):
    pass


class AssetIdentification(IdNameCombination):
    pass


class ExitReason(IdNameCombination):
    pass


class Origin(IdNameCombination):
    pass


class MonumentalProtectionType(IdNameCombination):
    pass


class District(IdNameCombination):
    pass


class ConstructionMethod(IdNameCombination):
    pass


class BuildingType(IdNameCombination):
    pass


class ChangeReason(IdNameCombination):
    pass


class StatusInventory(IdNameCombination):
    pass


class RegionalResponsibility(IdNameCombination):
    pass


class AddressType(IdNameCombination):
    pass


class EntryReason(IdNameCombination):
    pass


class Gender(IdNameCombination):
    pass


class ResidentalAuthorization(IdNameCombination):
    pass


class Position(IdNameCombination):
    pass


class ContractorType(IdNameCombination):
    pass


class Country:
    id_: int
    name: str
    code: str

    def __init__(self, id_: int, name: str, code: str) -> None:
        self.id_ = id_
        self.name = name
        self.code = code


class DunningData:
    dunningblock: bool

    def __init__(self, dunningblock: bool) -> None:
        self.dunningblock = dunningblock


class RestrictionOfUse:
    id_: int
    node_id: int
    name: str
    is_vacancy: bool

    def __init__(self, id_: int, node_id: int, name: str, is_vacancy: bool) -> None:
        self.id_ = id_
        self.node_id = node_id
        self.name = name
        self.is_vacancy = is_vacancy


class FinancingTypeClass:
    id_: int
    name: str
    classification_id: int
    classification_name: str

    def __init__(self, id_: int, name: str, classification_id: int, classification_name: str) -> None:
        self.id_ = id_
        self.name = name
        self.classification_id = classification_id
        self.classification_name = classification_name


class UseUnitUsageType:
    id_: int
    name: str
    classification_id: int
    classification_name: str

    def __init__(self, id_: int, classification_id: int, name: str = None,
                 classification_name: str = None) -> None:
        self.id_ = id_
        self.name = name
        self.classification_id = classification_id
        self.classification_name = classification_name


class UseUnitType:
    id_: int
    valid_from: datetime
    valid_to: datetime
    use_unit_usage_type: UseUnitUsageType

    def __init__(self, id_: int, valid_from: datetime,
                 use_unit_usage_type: Dict, valid_to: datetime = None) -> None:
        self.id_ = id_
        self.valid_from = valid_from
        self.valid_to = valid_to
        use_unit_usage_type["id_"] = use_unit_usage_type.pop("id")
        self.use_unit_usage_type = UseUnitUsageType(**use_unit_usage_type)


class UseUnitShort:
    id_: int
    use_unit_number: str
    building_land_id: int
    economic_unit_id: int
    economic_unit: str

    def __init__(self, id_: int, use_unit_number: str, building_land_id: int, economic_unit_id: int,
                 economic_unit: str) -> None:
        self.id_ = id_
        self.use_unit_number = use_unit_number
        self.building_land_id = building_land_id
        self.economic_unit_id = economic_unit_id
        self.economic_unit = economic_unit


class LicenseAgreement:
    id_: int
    id_num: str
    use_unit: UseUnitShort
    restriction_of_use: RestrictionOfUse
    status_contract: StatusContract
    life_of_contract: LifeOfContract
    payment_interval: PaymentInterval
    dunning_data: DunningData
    differing_maturity: int
    start_contract: datetime
    period_of_notice: PeriodOfNotice
    debit_entry_type: DebitEntryType

    def __init__(self, id_: int, id_num: str, use_unit: UseUnitShort, restriction_of_use: RestrictionOfUse,
                 status_contract: StatusContract, life_of_contract: LifeOfContract, payment_interval: PaymentInterval,
                 dunning_data: DunningData, start_contract: datetime,
                 debit_entry_type: DebitEntryType, period_of_notice: PeriodOfNotice = None,
                 differing_maturity: int = None,
                 **kwargs) -> None:
        self.id_ = id_
        self.id_num = id_num
        self.use_unit = use_unit
        self.restriction_of_use = restriction_of_use
        self.status_contract = status_contract
        self.life_of_contract = life_of_contract
        self.payment_interval = payment_interval
        self.dunning_data = dunning_data
        self.differing_maturity = differing_maturity
        self.start_contract = start_contract
        self.period_of_notice = period_of_notice
        self.debit_entry_type = debit_entry_type
        self.__dict__.update(kwargs)


class CollectiveAccount:
    no_real_bank_account: bool
    iban: str
    bic: str
    account_holder: str

    def __init__(self, no_real_bank_account: bool, iban: str, bic: str, account_holder: str) -> None:
        self.no_real_bank_account = no_real_bank_account
        self.iban = iban
        self.bic = bic
        self.account_holder = account_holder


class Banking:
    id_: int
    use_virtual_iban: bool
    virtual_iban: str
    former_virtual_iban: str
    collective_account: CollectiveAccount

    def __init__(self, id_: int, use_virtual_iban: bool, virtual_iban: str, former_virtual_iban: str,
                 collective_account: CollectiveAccount) -> None:
        self.id_ = id_
        self.use_virtual_iban = use_virtual_iban
        self.virtual_iban = virtual_iban
        self.former_virtual_iban = former_virtual_iban
        self.collective_account = collective_account


class CompanyCode:
    id_: int
    name: str
    code: str
    arge_code: Optional[str]

    def __init__(self, id_: int, name: str, code: str, arge_code: str = None) -> None:
        self.id_ = id_
        self.name = name
        self.code = code
        self.arge_code = arge_code


class Address:
    id_: int
    zip_: str
    town: str
    street: str
    house_number: str
    house_number_addition: str
    valid_from: datetime
    valid_to: datetime
    street_complete: str
    house_number_complete: str
    main_address: bool
    address_type: AdministrationType
    country: CompanyCode

    def __init__(self, id_: int, zip_: str, town: str, street: str, house_number: str,
                 valid_from: datetime, street_complete: str, house_number_complete: str,
                 main_address: bool, address_type: AdministrationType, country: CompanyCode,
                 house_number_addition: str = None, valid_to: datetime = None) -> None:
        self.id_ = id_
        self.zip_ = zip_
        self.town = town
        self.street = street
        self.house_number = house_number
        self.house_number_addition = house_number_addition
        self.valid_from = valid_from
        self.valid_to = valid_to
        self.street_complete = street_complete
        self.house_number_complete = house_number_complete
        self.main_address = main_address
        self.address_type = address_type
        self.country = country


class BankAccountType:
    id_: int
    code: str

    def __init__(self, id_: int, code: str) -> None:
        self.id_ = id_
        self.code = code


class BankAccountUsageType:
    id_: int
    code: str

    def __init__(self, id_: int, code: str) -> None:
        self.id_ = id_
        self.code = code


class BankAccount:
    id_: int
    bank_account_id: int
    iban: str
    bic: str
    account_holder: str
    valid_from: datetime
    valid_to: datetime
    bank_account_type: BankAccountType
    bank_account_usage_type: BankAccountUsageType

    def __init__(self, id_: int, bank_account_id: int, iban: str, bic: str, account_holder: str,
                 valid_from: datetime, valid_to: datetime, bank_account_type: Dict,
                 bank_account_usage_type: Dict) -> None:
        self.id_ = id_
        self.bank_account_id = bank_account_id
        self.iban = iban
        self.bic = bic
        self.account_holder = account_holder
        self.valid_from = valid_from
        self.valid_to = valid_to
        if "id" in bank_account_type.keys():
            bank_account_type["id_"] = bank_account_type.pop("id")
        self.bank_account_type = BankAccountType(**bank_account_type)
        if bank_account_usage_type is not None:
            if "id" in bank_account_usage_type.keys():
                bank_account_usage_type["id_"] = bank_account_usage_type.pop("id")
            self.bank_account_usage_type = BankAccountUsageType(**bank_account_usage_type)


class Communication:
    id_: int
    related_address_id: int
    content: str
    explanation: str
    related_address: str
    communication_type: CommunicationType

    def __init__(self, id_: int, related_address_id: int, content: str, explanation: str, related_address: str,
                 communication_type: Dict) -> None:
        self.id_ = id_
        self.related_address_id = related_address_id
        self.content = content
        self.explanation = explanation
        self.related_address = related_address
        self.communication_type = CommunicationType(**communication_type)


class LegalPerson:
    long_name1: str
    long_name2: str
    vat_id: str
    commercial_register_number: str
    commercial_register_town: str

    def __init__(self, long_name1: str, long_name2: str = None, vat_id: str = None,
                 commercial_register_number: str = None,
                 commercial_register_town: str = None) -> None:
        self.long_name1 = long_name1
        self.long_name2 = long_name2
        self.vat_id = vat_id
        self.commercial_register_number = commercial_register_number
        self.commercial_register_town = commercial_register_town


class NaturalPerson:
    first_name: str
    last_name: str
    birth_date: datetime
    gender: Gender

    def __init__(self, first_name: str, last_name: str, birth_date: datetime, gender: Dict) -> None:
        self.first_name = first_name
        self.last_name = last_name
        self.birth_date = birth_date
        self.gender = Gender(**gender)


class Person:
    id_: int
    id_num: str
    shortname: str
    name: str
    tax_number: str
    tax_identification_number: str
    valid_from: datetime
    valid_to: datetime
    is_natural_person: bool
    natural_person: Optional[NaturalPerson]
    legal_person: Optional[LegalPerson]
    addresses: List[Address]
    communications: Optional[List[Communication]]
    bank_accounts: Optional[List[BankAccount]]
    first_email_communication: Optional[Communication]
    first_landline_phone_communication: Optional[Communication]
    first_mobile_phone_communication: Optional[Communication]

    def __init__(self, id_: int, id_num: str, shortname: str, name: str,
                 valid_from: datetime, is_natural_person: bool,
                 addresses: List[Dict],
                 bank_accounts: List[Dict] = None,
                 first_email_communication: Dict = None, first_landline_phone_communication: Dict = None,
                 first_mobile_phone_communication: Dict = None, communications: List[Dict] = None,
                 legal_person: Dict = None, natural_person: Dict = None,
                 valid_to: datetime = None, tax_identification_number: str = None,
                 tax_number: str = None, **kwargs) -> None:
        self.id_ = id_
        self.id_num = id_num
        self.shortname = shortname
        self.name = name
        self.tax_number = tax_number
        self.tax_identification_number = tax_identification_number
        self.valid_from = valid_from
        self.valid_to = valid_to
        self.is_natural_person = is_natural_person
        if natural_person is not None:
            self.natural_person = NaturalPerson(**natural_person)
        else:
            self.natural_person = None
        if legal_person is not None:
            self.legal_person = LegalPerson(**legal_person)
        else:
            self.legal_person = None
        taddresses = []
        if len(addresses) > 0:
            for entry in addresses:
                entry["id_"] = entry.pop("id")
                entry["zip_"] = entry.pop("zip")
                taddress = Address(**entry)
                taddresses.append(taddress)
        self.addresses = taddresses

        tcommunications = []
        if communications is not None and len(communications) > 0:
            for entry in communications:
                if "id" in entry.keys():
                    entry["id_"] = entry.pop("id")
                tcommunication = Communication(**entry)
                tcommunications.append(tcommunication)
            self.communications = tcommunications
        else:
            self.communications = None

        taccounts = []
        if bank_accounts is not None and len(bank_accounts) > 0:
            for entry in bank_accounts:
                if "id" in entry.keys():
                    entry["id_"] = entry.pop("id")
                taccount = BankAccount(**entry)
                taccounts.append(taccount)
            self.bank_accounts = taccounts
        else:
            self.bank_accounts = None

        if first_email_communication is not None:
            if "id" in first_email_communication.keys():
                first_email_communication["id_"] = first_email_communication.pop("id")
            self.first_email_communication = Communication(**first_email_communication)
        else:
            self.first_email_communication = None
        if first_landline_phone_communication is not None:
            if "id" in first_landline_phone_communication.keys():
                first_landline_phone_communication["id_"] = first_landline_phone_communication.pop("id")
            self.first_landline_phone_communication = Communication(**first_landline_phone_communication)
        else:
            self.first_landline_phone_communication = None
        if first_mobile_phone_communication is not None:
            if "id" in first_mobile_phone_communication.keys():
                first_mobile_phone_communication["id_"] = first_mobile_phone_communication.pop("id")
            self.first_mobile_phone_communication = Communication(**first_mobile_phone_communication)
        else:
            self.first_mobile_phone_communication = None
        self.__dict__.update(kwargs)


class Management:
    id_: int
    id_num: str
    name: str
    node_id: int
    parent_management_id: int
    administration_type: AdministrationType
    person: Person
    default_address: Address
    default_bankaccount: BankAccount
    company_codes: List[CompanyCode]

    def __init__(self, id_: int, id_num: str, name: str, node_id: int, parent_management_id: int,
                 administration_type: AdministrationType, person: Person,
                 company_codes: List[CompanyCode], default_bankaccount: BankAccount = None,
                 default_address: Address = None, **kwargs) -> None:
        self.id_ = id_
        self.id_num = id_num
        self.name = name
        self.node_id = node_id
        self.parent_management_id = parent_management_id
        self.administration_type = administration_type
        self.person = person
        self.default_address = default_address
        self.default_bankaccount = default_bankaccount
        self.company_codes = company_codes
        self.__dict__.update(kwargs)


class OwnerShort:
    id_: int
    owner_number: str

    def __init__(self, id_: int, owner_number: str) -> None:
        self.id_ = id_
        self.owner_number = owner_number


class EconomicUnitShort:
    id_: int
    id_num: str
    name: str
    location: str

    def __init__(self, id_: int, id_num: str, name: str, location: str = None, **kwargs) -> None:
        self.id_ = id_
        self.id_num = id_num
        self.name = name
        self.location = location
        self.__dict__.update(kwargs)


class EconomicUnit:
    id_: int
    id_num: str
    name: str
    location: str
    construction_year: int
    info: str
    binding_end_date: datetime
    owner: OwnerShort
    asset_identification: Optional[AssetIdentification]
    status_inventory: Optional[StatusInventory]
    district: Optional[District]
    monumental_protection_type: Optional[MonumentalProtectionType]
    regional_responsibility: Optional[RegionalResponsibility]
    company_code: Optional[CompanyCode]

    def __init__(self, id_: int, id_num: str, name: str, construction_year: int,
                 owner: Dict, asset_identification: Dict,
                 status_inventory: Dict,
                 company_code: Dict, district: Dict = None, location: str = None,
                 regional_responsibility: Dict = None, binding_end_date: datetime = None,
                 info: str = None, monumental_protection_type: Dict = None, **kwargs) -> None:
        self.id_ = id_
        self.id_num = id_num
        self.name = name
        self.location = location
        self.construction_year = construction_year
        self.info = info
        self.binding_end_date = binding_end_date
        owner["id_"] = owner.pop("id")
        self.owner = OwnerShort(**owner)
        if asset_identification is not None:
            asset_identification["id_"] = asset_identification.pop("id")
            self.asset_identification = AssetIdentification(**asset_identification)
        else:
            self.asset_identification = None
        if status_inventory is not None:
            status_inventory["id_"] = status_inventory.pop("id")
            self.status_inventory = StatusInventory(**status_inventory)
        else:
            self.status_inventory = None
        if district is not None:
            district["id_"] = district.pop("id")
            self.district = District(**district)
        else:
            self.district = None
        if monumental_protection_type is not None:
            monumental_protection_type["id_"] = monumental_protection_type.pop("id")
            self.monumental_protection_type = MonumentalProtectionType(**monumental_protection_type)
        else:
            self.monumental_protection_type = None
        if regional_responsibility is not None:
            regional_responsibility["id_"] = regional_responsibility.pop("id")
            self.regional_responsibility = RegionalResponsibility(**regional_responsibility)
        else:
            self.regional_responsibility = None
        if company_code is not None:
            company_code["id_"] = company_code.pop("id")
            self.company_code = CompanyCode(**company_code)
        else:
            self.company_code = None
        self.__dict__.update(kwargs)


class Building:
    construction_year: int
    move_in_date: datetime
    building_number_of_storeys: int
    construction_method: Optional[ConstructionMethod]
    building_type: BuildingType
    district: Optional[District]
    monumental_protection_type: Optional[MonumentalProtectionType]
    origin: Origin
    change_reason: Optional[ChangeReason]

    def __init__(self, origin: Dict,
                 building_type: Dict, move_in_date: datetime = None, construction_year: int = None,
                 construction_method: Dict = None, district: Dict = None,
                 monumental_protection_type: Dict = None, change_reason: Dict = None,
                 building_number_of_storeys: int = None) -> None:
        self.construction_year = construction_year
        self.move_in_date = move_in_date
        self.building_number_of_storeys = building_number_of_storeys
        if construction_method is not None:
            construction_method["id_"] = construction_method.pop("id")
            self.construction_method = ConstructionMethod(**construction_method)
        else:
            self.construction_method = None
        self.building_type = BuildingType(**building_type)
        if district is not None:
            district["id_"] = district.pop("id")
            self.district = District(**district)
        else:
            self.district = None
        if monumental_protection_type is not None:
            self.monumental_protection_type = MonumentalProtectionType(**monumental_protection_type)
        else:
            self.monumental_protection_type = None
        self.origin = Origin(**origin)
        if change_reason is not None:
            self.change_reason = ChangeReason(**change_reason)
        else:
            self.change_reason = None


class Floor:
    id_: int
    name: str
    level_to_ground: int

    def __init__(self, id_: int, name: str, level_to_ground: int) -> None:
        self.id_ = id_
        self.name = name
        self.level_to_ground = level_to_ground


class EstateAddress:
    zip_: str
    town: str
    street: str
    house_number: str
    house_number_addition: str
    country_id: int
    country_code: str
    street_complete: str
    house_number_complete: str

    def __init__(self, zip_: str, town: str, street: str, house_number: str,
                 country_id: int, country_code: str, street_complete: str, house_number_complete: str,
                 house_number_addition: str = None) -> None:
        self.zip_ = zip_
        self.town = town
        self.street = street
        self.house_number = house_number
        self.house_number_addition = house_number_addition
        self.country_id = country_id
        self.country_code = country_code
        self.street_complete = street_complete
        self.house_number_complete = house_number_complete


class Land:
    land_area: int
    entry_reason: ExitReason

    def __init__(self, land_area: int, entry_reason: ExitReason) -> None:
        self.land_area = land_area
        self.entry_reason = entry_reason


class BuildingLand:
    id_: int
    id_num: str
    building_land_type: int
    entry_date: datetime
    exit_date: datetime
    economic_unit: EconomicUnitShort
    estate_address: EstateAddress
    land: Optional[Land]
    building: Building
    exit_reason: Optional[ExitReason]

    def __init__(self, id_: int, id_num: str, building_land_type: int, entry_date: datetime,
                 economic_unit: Dict,
                 estate_address: Dict, building: Dict, land: Dict = None,
                 exit_date: datetime = None, exit_reason: Dict = None, **kwargs) -> None:
        self.id_ = id_
        self.id_num = id_num
        self.building_land_type = building_land_type
        self.entry_date = entry_date
        self.exit_date = exit_date
        economic_unit['id_'] = economic_unit.pop('id')
        self.economic_unit = EconomicUnitShort(**economic_unit)
        self.estate_address = EstateAddress(**estate_address)
        if land is not None:
            self.land = Land(**land)
        else:
            self.land = None
        self.building = Building(**building)
        if exit_reason is not None:
            self.exit_reason = ExitReason(**exit_reason)
        else:
            self.exit_reason = None
        self.__dict__.update(kwargs)


class BuildingLandShort:
    id_: int
    id_num: str
    building_land_type: str

    def __init__(self, id_: int, id_num: str, building_land_type: str) -> None:
        self.id_ = id_
        self.id_num = id_num
        self.building_land_type = building_land_type


class Owner:
    id_: int
    owner_number: str
    is_condominium: bool
    person: Person
    default_address: Address
    default_bankaccount: Optional[BankAccount]
    company_codes: List[CompanyCode]

    def __init__(self, id_: int, owner_number: str, is_condominium: bool,
                 person: Dict, default_address: Dict,
                 default_bankaccount: Dict = None, company_codes: List[Dict] = None, **kwargs) -> None:
        self.id_ = id_
        self.owner_number = owner_number
        self.is_condominium = is_condominium
        person["id_"] = person.pop("id")
        self.person = Person(**person)
        if default_bankaccount is not None:
            default_bankaccount["id_"] = default_bankaccount.pop("id")
            self.default_bankaccount = BankAccount(**default_bankaccount)
        else:
            self.default_bankaccount = None

        default_address["id_"] = default_address.pop("id")
        default_address["zip_"] = default_address.pop("zip")
        self.default_address = Address(**default_address)

        tcodes = []
        if company_codes is not None and len(company_codes) > 0:
            for entry in company_codes:
                tcode = CompanyCode(**entry)
                tcodes.append(tcode)

        self.company_codes = tcodes
        self.__dict__.update(kwargs)


class BillingUnit:
    id_: int
    value: int
    valid_from: datetime
    valid_to: datetime
    is_base_component_cold_water: bool
    is_base_component_heating: bool
    is_base_component_warm_water: bool
    quantity_type: CompanyCode

    def __init__(self, id_: int, value: int, valid_from: datetime,
                 is_base_component_cold_water: bool, is_base_component_heating: bool,
                 is_base_component_warm_water: bool, quantity_type: Dict,
                 valid_to: datetime = None) -> None:
        self.id_ = id_
        self.value = value
        self.valid_from = valid_from
        self.valid_to = valid_to
        self.is_base_component_cold_water = is_base_component_cold_water
        self.is_base_component_heating = is_base_component_heating
        self.is_base_component_warm_water = is_base_component_warm_water
        self.quantity_type = CompanyCode(**quantity_type)


class UseUnit:
    id_: int
    id_num: str
    building_land: BuildingLandShort
    economic_unit: EconomicUnitShort
    estate_address: EstateAddress
    financing_type: FinancingTypeClass
    current_use_unit_type: UseUnitType
    usable_space: int
    living_space: int
    heating_space: int
    number_of_rooms: int
    number_of_half_rooms: int
    description_of_position: str
    target_rent: int
    management_start: datetime
    management_end: datetime
    binding_end_date: datetime
    move_in_date: datetime
    exit_date: datetime
    entry_date: datetime
    energy_certificate_id: int
    position: Optional[Position]
    floor: Optional[Floor]
    residential_authorization: Optional[ResidentalAuthorization]
    entry_reason: EntryReason
    exit_reason: Optional[ExitReason]
    billing_units: List[BillingUnit]
    use_unit_types: List[UseUnitType]
    company_code: CompanyCode

    def __init__(self, id_: int, id_num: str,
                 building_land: Dict, economic_unit: Dict,
                 estate_address: Dict, financing_type: Dict,
                 current_use_unit_type: Dict, usable_space: int,
                 living_space: int, heating_space: int,
                 management_start: datetime,
                 entry_date: datetime,
                 entry_reason: Dict,
                 use_unit_types: List[UseUnitType], number_of_half_rooms: int = None,
                 move_in_date: datetime = None, number_of_rooms: int = None, position: Dict = None,
                 floor: Dict = None,
                 energy_certificate_id: int = None, description_of_position: str = None,
                 exit_reason: Dict = None, billing_units: List[BillingUnit] = None,
                 company_code: CompanyCode = None, binding_end_date: datetime = None, exit_date: datetime = None,
                 management_end: datetime = None, target_rent: int = None,
                 residential_authorization: Dict = None, **kwargs) -> None:
        self.id_ = id_
        self.id_num = id_num
        building_land["id_"] = building_land.pop("id")
        self.building_land = BuildingLandShort(**building_land)
        economic_unit["id_"] = economic_unit.pop("id")
        self.economic_unit = EconomicUnitShort(**economic_unit)
        self.estate_address = EstateAddress(**estate_address)
        financing_type["id_"] = financing_type.pop("id")
        self.financing_type = FinancingTypeClass(**financing_type)
        current_use_unit_type["id_"] = current_use_unit_type.pop("id")
        self.current_use_unit_type = UseUnitType(**current_use_unit_type)
        self.usable_space = usable_space
        self.living_space = living_space
        self.heating_space = heating_space
        self.number_of_rooms = number_of_rooms
        self.number_of_half_rooms = number_of_half_rooms
        self.description_of_position = description_of_position
        self.target_rent = target_rent
        self.management_start = management_start
        self.management_end = management_end
        self.binding_end_date = binding_end_date
        self.move_in_date = move_in_date
        self.exit_date = exit_date
        self.entry_date = entry_date
        self.energy_certificate_id = energy_certificate_id
        if position is not None:
            position["id_"] = position.pop("id")
            self.position = Position(**position)
        else:
            self.position = None
        if floor is not None:
            self.floor = Floor(**floor)
        else:
            self.floor = None
        if residential_authorization is not None:
            self.residential_authorization = ResidentalAuthorization(**residential_authorization)
        else:
            self.residential_authorization = None
        self.entry_reason = EntryReason(**entry_reason)
        if exit_reason is not None:
            self.exit_reason = ExitReason(**exit_reason)
        else:
            self.exit_reason = None
        self.billing_units = billing_units
        self.use_unit_types = use_unit_types
        self.company_code = company_code
        self.__dict__.update(kwargs)


class Contractor:
    id_: int
    license_agreement_id: int
    license_agreement: str
    start_contract: datetime
    end_of_contract: datetime
    contractual_use_valid_from: datetime
    contractual_use_valid_to: datetime
    contractor_type: ContractorType
    use_unit: UseUnitShort
    person: Person
    default_address: Address

    def __init__(self, id_: int, license_agreement_id: int,
                 license_agreement: str, start_contract: datetime,
                 end_of_contract: datetime, contractual_use_valid_from: datetime,
                 contractual_use_valid_to: datetime, contractor_type: Dict,
                 use_unit: Dict, person: Dict, default_address: Dict) -> None:
        self.id_ = id_
        self.license_agreement_id = license_agreement_id
        self.license_agreement = license_agreement
        self.start_contract = start_contract
        self.end_of_contract = end_of_contract
        self.contractual_use_valid_from = contractual_use_valid_from
        self.contractual_use_valid_to = contractual_use_valid_to
        self.contractor_type = ContractorType(**contractor_type)
        use_unit["id_"] = use_unit.pop("id")
        self.use_unit = UseUnitShort(**use_unit)
        person["id_"] = person.pop("id")
        self.person = Person(**person)
        default_address["id_"] = default_address.pop("id")
        default_address["zip_"] = default_address.pop("zip")
        self.default_address = Address(**default_address)
