from typing import List, Dict, Optional
from datetime import datetime


class Result:
    def __init__(self, status_code: int, message: str = '', data: List[Dict] = None):
        self.status_code = int(status_code)
        self.message = str(message)
        self.data = data if data else []


class CraftActivity:
    id_: int
    code: str

    def __init__(self, id_: int, code: str) -> None:
        self.id_ = id_
        self.code = code


class PaymentFileStatus:
    id_: int
    code: str

    def __init__(self, id_: int, code: str) -> None:
        self.id_ = id_
        self.code = code


class SalesTax:
    id_: int
    code: str

    def __init__(self, id_: int, code: str) -> None:
        self.id_ = id_
        self.code = code


class CommissionType:
    id_: int
    code: str

    def __init__(self, id_: int, code: str) -> None:
        self.id_ = id_
        self.code = code


class CommissionStatus:
    id_: int
    code: str

    def __init__(self, id_: int, code: str) -> None:
        self.id_ = id_
        self.code = code


class Commission:
    id_: int
    id_num: str
    code: str
    recording_date: datetime
    release_date: datetime
    placing_date: Optional[datetime]
    acceptance_date: Optional[datetime]
    completion_date: Optional[datetime]
    commission_type: CommissionType
    commission_status: CommissionStatus

    def __init__(self, id_: int,
                 id_num: str,
                 code: str,
                 recording_date: str,
                 release_date: str,
                 placing_date: str,
                 acceptance_date: str,
                 completion_date: str,
                 commission_type: Dict,
                 commission_status: Dict) -> None:
        self.id_ = id_
        self.id_num = id_num
        self.code = code
        self.recording_date = datetime.strptime(recording_date, "%Y-%m-%dT%H:%M:%S%z")
        if '.' in release_date:
            self.release_date = datetime.strptime(release_date, "%Y-%m-%dT%H:%M:%S.%f%z")
        else:
            self.release_date = datetime.strptime(release_date, "%Y-%m-%dT%H:%M:%S%z")
        if placing_date is not None:
            if '.' in placing_date:
                self.placing_date = datetime.strptime(placing_date, "%Y-%m-%dT%H:%M:%S.%f%z")
            else:
                self.placing_date = datetime.strptime(placing_date, "%Y-%m-%dT%H:%M:%S%z")
        else:
            self.placing_date = None
        if acceptance_date is not None:
            self.acceptance_date = datetime.strptime(acceptance_date, "%Y-%m-%dT%H:%M:%S.%f%z")
        else:
            self.acceptance_date = None
        if completion_date is not None:
            if '.' in completion_date:
                self.completion_date = datetime.strptime(completion_date, "%Y-%m-%dT%H:%M:%S.%f%z")
            else:
                self.completion_date = datetime.strptime(completion_date, "%Y-%m-%dT%H:%M:%S%z")
        else:
            self.completion_date = None
        commission_type["id_"] = commission_type.pop("id")
        self.commission_type = CommissionType(**commission_type)
        commission_status["id_"] = commission_status.pop("id")
        self.commission_status = CommissionStatus(**commission_status)


class Component:
    id_: int
    name: str

    def __init__(self, id_: int, name: str) -> None:
        self.id_ = id_
        self.name = name


class Facility:
    id_: int
    name: str

    def __init__(self, id_: int, name: str) -> None:
        self.id_ = id_
        self.name = name


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


class ChangeReasonContracts(IdNameCombination):
    pass


class ValidContractPosition(IdNameCombination):
    pass


class ContractPositionType:
    id_: int
    node_id: int
    name: str
    short_code: str
    deposit: bool
    wb_relevant: bool
    bgb_relevant: bool
    is_part_of_net_rent: bool
    using_cp_as_prepayment_block: bool
    assignment_prepayment: str
    is_gross_rent_without_heating: bool
    is_part_of_net_rent_census: bool
    is_basis_calculation_reminder_charge_interest: bool
    is_prepayment_heating: bool
    is_prepayment_running_cost: bool
    report_as_sinking_fund: bool

    def __init__(self, id_: int, node_id: int, name: str, short_code: str, deposit: bool, wb_relevant: bool,
                 bgb_relevant: bool, is_part_of_net_rent: bool, using_cp_as_prepayment_block: bool,
                 assignment_prepayment: str, is_gross_rent_without_heating: bool, is_part_of_net_rent_census: bool,
                 is_basis_calculation_reminder_charge_interest: bool, is_prepayment_heating: bool,
                 is_prepayment_running_cost: bool, report_as_sinking_fund: bool) -> None:
        self.id_ = id_
        self.node_id = node_id
        self.name = name
        self.short_code = short_code
        self.deposit = deposit
        self.wb_relevant = wb_relevant
        self.bgb_relevant = bgb_relevant
        self.is_part_of_net_rent = is_part_of_net_rent
        self.using_cp_as_prepayment_block = using_cp_as_prepayment_block
        self.assignment_prepayment = assignment_prepayment
        self.is_gross_rent_without_heating = is_gross_rent_without_heating
        self.is_part_of_net_rent_census = is_part_of_net_rent_census
        self.is_basis_calculation_reminder_charge_interest = is_basis_calculation_reminder_charge_interest
        self.is_prepayment_heating = is_prepayment_heating
        self.is_prepayment_running_cost = is_prepayment_running_cost
        self.report_as_sinking_fund = report_as_sinking_fund


class ContractPositionTypeSlim:
    id_: int
    name: str
    short_code: str

    def __init__(self, id_: int, name: str, short_code: str) -> None:
        self.id_ = id_
        self.name = name
        self.short_code = short_code


class Country:
    id_: int
    name: str
    code: str

    def __init__(self, id_: int, name: str, code: str) -> None:
        self.id_ = id_
        self.name = name
        self.code = code


class DunningLevel:
    id_: int
    code: str

    def __init__(self, id_: int, code: str) -> None:
        self.id_ = id_
        self.code = code


class Budget:
    id_: int
    code: str

    def __init__(self, id_: int, code: str) -> None:
        self.id_ = id_
        self.code = code


class BudgetDetail:
    id_: int
    budget_id: int
    hierarchy1_value: str
    hierarchy2_value: str
    hierarchy3_value: str

    def __init__(self, id_: int, budget_id: int, hierarchy1_value: str,
                 hierarchy2_value: str, hierarchy3_value: str) -> None:
        self.id_ = id_
        self.budget_id = budget_id
        self.hierarchy1_value = hierarchy1_value
        self.hierarchy2_value = hierarchy2_value
        self.hierarchy3_value = hierarchy3_value


class BudgetData:
    budget: Budget
    budget_detail: BudgetDetail

    def __init__(self, budget: Dict, budget_detail: Dict):
        self.budget = Budget(**budget)
        self.budget_detail = BudgetDetail(**budget_detail)


class DunningData:
    dunningblock: bool
    dunning_level: Optional[DunningLevel]

    def __init__(self, dunningblock: bool, dunning_level: Dict = None) -> None:
        self.dunningblock = dunningblock
        if dunning_level is not None:
            dunning_level["id_"] = dunning_level.pop("id")
            self.dunning_level = DunningLevel(**dunning_level)
        else:
            self.dunning_level = None


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


class UseUnitTypeCatalogEntry:
    id_: int
    name: str
    classification: str

    def __init__(self, id_: int, name: str, classification: str):
        self.id_ = id_
        self.name = name
        self.classification = classification


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

    def __init__(self, id_: int, use_unit_number: str, building_land_id: int = 0, economic_unit_id: int = 0,
                 economic_unit: str = 0) -> None:
        self.id_ = id_
        self.use_unit_number = use_unit_number
        self.building_land_id = building_land_id
        self.economic_unit_id = economic_unit_id
        self.economic_unit = economic_unit


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


class QuantityType:
    id_: int
    name: str
    code: str
    arge_code: Optional[str]

    def __init__(self, id_: int, name: str, code: str, arge_code: str = None) -> None:
        self.id_ = id_
        self.name = name
        self.code = code
        self.arge_code = arge_code


class ServiceCatalogue:
    id_: int
    id_num: str
    description: str
    quantity_type: Optional[QuantityType]

    def __init__(self, id_: int, id_num: str, description: str, quantity_type: Dict) -> None:
        self.id_ = id_
        self.id_num = id_num
        self.description = description
        if quantity_type is not None:
            self.quantity_type = QuantityType(**quantity_type)
        else:
            self.quantity_type = None


class CommissionItem:
    id_: int
    code: str
    unit_price: int
    gross_amount: int
    net_amount: int
    units: int
    commission_text: str
    internal_description: str
    position_number: int
    budget_data: Optional[BudgetData]
    sales_tax: SalesTax
    service_catalogue: ServiceCatalogue
    craft_activity: CraftActivity
    quantity_type: Optional[QuantityType]
    component: Optional[Component]
    facility: Optional[Facility]
    approved_net_amount: int
    commission: Commission

    def __init__(self, id_: int,
                 code: str,
                 unit_price: int,
                 gross_amount: int,
                 net_amount: int,
                 units: int,
                 commission_text: str,
                 internal_description: str,
                 position_number: int,
                 budget_data: Dict,
                 sales_tax: Dict,
                 service_catalogue: Dict,
                 craft_activity: Dict,
                 quantity_type: Dict,
                 component: Dict,
                 facility: Dict,
                 approved_net_amount: int,
                 commission: Dict) -> None:
        self.id_ = id_
        self.code = code
        self.unit_price = unit_price
        self.gross_amount = gross_amount
        self.net_amount = net_amount
        self.units = units
        self.commission_text = commission_text
        self.internal_description = internal_description
        self.position_number = position_number
        if budget_data is not None:
            budget_data["id_"] = budget_data.pop("id")
            self.budget_data = BudgetData(**budget_data)
        else:
            self.budget_data = None
        sales_tax["id_"] = sales_tax.pop("id")
        self.sales_tax = SalesTax(**sales_tax)
        service_catalogue["id_"] = service_catalogue.pop("id")
        self.service_catalogue = ServiceCatalogue(**service_catalogue)
        craft_activity["id_"] = craft_activity.pop("id")
        self.craft_activity = CraftActivity(**craft_activity)
        if quantity_type is not None:
            quantity_type["id_"] = quantity_type.pop("id")
            self.quantity_type = QuantityType(**quantity_type)
        else:
            self.quantity_type = None
        if component is not None:
            component["id_"] = component.pop("id")
            self.component = Component(**component)
        else:
            self.component = None
        if facility is not None:
            facility["id_"] = facility.pop("id")
            self.facility = Facility(**facility)
        else:
            self.facility = None
        self.approved_net_amount = approved_net_amount
        commission["id_"] = commission.pop("id")
        self.commission = Commission(**commission)


class PaymentOrderElement:
    payment_order_number: str
    maturity: datetime
    transfer_date: datetime
    payment_file_status: PaymentFileStatus

    def __init__(self,
                 payment_order_number: str,
                 maturity: str,
                 transfer_date: str,
                 payment_file_status: Dict) -> None:
        self.payment_order_number = payment_order_number
        self.maturity = datetime.strptime(maturity, "%Y-%m-%d")
        self.transfer_date = datetime.strptime(transfer_date, "%Y-%m-%d")
        payment_file_status["id_"] = payment_file_status.pop("id")
        self.payment_file_status = PaymentFileStatus(**payment_file_status)


class TaxSubtotal:
    net: int
    vat: int
    tax_id: int
    tax_code: str

    def __init__(self, net: int, vat: int, tax_id: int, tax_code: str) -> None:
        self.net = net
        self.vat = vat
        self.tax_id = tax_id
        self.tax_code = tax_code


class TaxTotal:
    tax_amount: int
    tax_subtotals: List[TaxSubtotal]

    def __init__(self, tax_amount: int, tax_subtotals: List[Dict]) -> None:
        self.tax_amount = tax_amount
        self.tax_subtotals = []
        if tax_subtotals is not None:
            for subtotal_entry in tax_subtotals:
                ttax_item = subtotal_entry.get("tax")
                if ttax_item is not None:
                    ttax_id = ttax_item.get("id")
                    ttax_code = ttax_item.get("code")
                else:
                    ttax_id = -1
                    ttax_code = ""
                subtotal_obj = TaxSubtotal(subtotal_entry.get("net"),
                                           subtotal_entry.get("vat"),
                                           ttax_id,
                                           ttax_code)
                self.tax_subtotals.append(subtotal_obj)


class MonetaryTotal:
    tax_exclusive_amount: int
    tax_inclusive_amount: int
    labor_cost: int
    material_cost: int

    def __init__(self, tax_exclusive_amount: int, tax_inclusive_amount: int, labor_cost: int,
                 material_cost: int) -> None:
        self.tax_exclusive_amount = tax_exclusive_amount
        self.tax_inclusive_amount = tax_inclusive_amount
        self.labor_cost = labor_cost
        self.material_cost = material_cost


class InvoiceReceipt:
    id_: int
    number: str
    company_code: CompanyCode
    payment_orders: List[PaymentOrderElement]
    invoice_date: datetime
    maturity_date: datetime
    monetary_total: MonetaryTotal
    tax_total: TaxTotal
    commission_items: List[CommissionItem]

    def __init__(self, id_: int,
                 number: str,
                 company_code: Dict,
                 invoice_date: str,
                 maturity_date: str,
                 monetary_total: Dict,
                 tax_total: Dict,
                 payment_orders: List[Dict],
                 commission_items: List[Dict]) -> None:
        self.id_ = id_
        self.number = number
        company_code["id_"] = company_code.pop("id")
        self.company_code = CompanyCode(**company_code)
        if '.' in invoice_date:
            self.invoice_date = datetime.strptime(invoice_date, "%Y-%m-%dT%H:%M:%S.%f%z")
        else:
            self.invoice_date = datetime.strptime(invoice_date, "%Y-%m-%dT%H:%M:%S%z")
        if '.' in maturity_date:
            self.maturity_date = datetime.strptime(maturity_date, "%Y-%m-%dT%H:%M:%S.%f%z")
        else:
            self.maturity_date = datetime.strptime(maturity_date, "%Y-%m-%dT%H:%M:%S%z")
        self.monetary_total = MonetaryTotal(**monetary_total)
        self.tax_total = TaxTotal(**tax_total)
        tpayment_orders = []
        if payment_orders is not None:
            for payment_order in payment_orders:
                payment_order_obj = PaymentOrderElement(**payment_order)
                tpayment_orders.append(payment_order_obj)
        self.payment_orders = tpayment_orders
        tcommission_items = []
        if commission_items is not None:
            for commission_item in commission_items:
                commission_item["id_"] = commission_item.pop("id")
                commission_item_obj = CommissionItem(**commission_item)
                tcommission_items.append(commission_item_obj)
        self.commission_items = tcommission_items


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
    gender: Optional[Gender]

    def __init__(self, first_name: str, last_name: str, birth_date: datetime, gender: Dict = None) -> None:
        self.first_name = first_name
        self.last_name = last_name
        self.birth_date = birth_date
        if gender is not None:
            self.gender = Gender(**gender)
        else:
            self.gender = None


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
        if addresses is not None and len(addresses) > 0:
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
    company_code: Optional[CompanyCode]

    def __init__(self, id_: int, id_num: str, building_land_type: int, entry_date: datetime,
                 economic_unit: Dict,
                 estate_address: Dict, building: Dict, land: Dict = None,
                 exit_date: datetime = None, exit_reason: Dict = None, company_code: Dict = None,
                 **kwargs) -> None:
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
        if company_code is not None:
            company_code['id_'] = company_code.pop('id')
            self.company_code = CompanyCode(**company_code)
        else:
            self.company_code = None
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


class LicenseAgreementShort:
    id_: int
    id_num: str
    use_unit: UseUnitShort

    def __init__(self, id_: int, id_num: str, use_unit: Dict) -> None:
        self.id_ = id_
        self.id_num = id_num
        use_unit["id_"] = use_unit.pop("id")
        self.use_unit = UseUnitShort(**use_unit)


class VatRate:
    id_: int
    code: str

    def __init__(self, id_: int, code: str) -> None:
        self.id_ = id_
        self.code = code


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
    period_of_notice: Optional[PeriodOfNotice]
    debit_entry_type: DebitEntryType
    contractors: Optional[List[Contractor]]

    def __init__(self, id_: int, id_num: str, use_unit: Dict, restriction_of_use: Dict,
                 status_contract: Dict, life_of_contract: Dict, payment_interval: Dict,
                 dunning_data: Dict, start_contract: datetime,
                 debit_entry_type: Dict,
                 period_of_notice: Dict = None, contractors: List[Contractor] = None,
                 differing_maturity: int = None,
                 **kwargs) -> None:
        self.id_ = id_
        self.id_num = id_num
        use_unit["id_"] = use_unit.pop("id")
        self.use_unit = UseUnitShort(**use_unit)
        restriction_of_use["id_"] = restriction_of_use.pop("id")
        self.restriction_of_use = RestrictionOfUse(**restriction_of_use)
        status_contract["id_"] = status_contract.pop("id")
        self.status_contract = StatusContract(**status_contract)
        life_of_contract["id_"] = life_of_contract.pop("id")
        self.life_of_contract = LifeOfContract(**life_of_contract)
        payment_interval["id_"] = payment_interval.pop("id")
        self.payment_interval = PaymentInterval(**payment_interval)
        self.dunning_data = DunningData(**dunning_data)
        self.differing_maturity = differing_maturity
        self.start_contract = start_contract
        if period_of_notice is not None:
            period_of_notice["id_"] = period_of_notice.pop("id")
            self.period_of_notice = PeriodOfNotice(**period_of_notice)
        else:
            self.period_of_notice = None
        self.debit_entry_type = DebitEntryType(**debit_entry_type)
        self.contractors = contractors
        self.__dict__.update(kwargs)


class ContractPosition:
    id_: int
    net_amount: int
    amount: int
    active_from: datetime
    active_to: datetime
    license_agreement: LicenseAgreementShort
    vat_rate: VatRate
    valid_contract_position: ValidContractPosition
    change_reason_contracts: ChangeReasonContracts
    contract_position_type: ContractPositionType
    contract_position_type_slim: Optional[ContractPositionTypeSlim]

    def __init__(self, id_: int, net_amount: int, amount: int, active_from: datetime,
                 active_to: datetime, license_agreement: Dict,
                 vat_rate: Dict, valid_contract_position: Dict,
                 change_reason_contracts: Dict,
                 contract_position_type: Dict,
                 contract_position_type_slim: Dict) -> None:
        self.id_ = id_
        self.net_amount = net_amount
        self.amount = amount
        self.active_from = active_from
        self.active_to = active_to
        license_agreement["id_"] = license_agreement.pop("id")
        self.license_agreement = LicenseAgreementShort(**license_agreement)
        vat_rate["id_"] = vat_rate.pop("id")
        self.vat_rate = VatRate(**vat_rate)
        valid_contract_position["id_"] = valid_contract_position.pop("id")
        self.valid_contract_position = ValidContractPosition(**valid_contract_position)
        change_reason_contracts["id_"] = change_reason_contracts.pop("id")
        self.change_reason_contracts = ChangeReasonContracts(**change_reason_contracts)
        contract_position_type["id_"] = contract_position_type.pop("id")
        self.contract_position_type = ContractPositionType(**contract_position_type)
        if contract_position_type_slim is not None:
            contract_position_type_slim["id_"] = contract_position_type_slim.pop("id")
            self.contract_position_type_slim = ContractPositionTypeSlim(**contract_position_type_slim)
        else:
            self.contract_position_type_slim = None


class TicketComment:
    id_: int
    created_at: datetime
    content: str
    user_name: str

    def __init__(self, id_: int, created_at: str, content: str, user_name: str) -> None:
        self.id_ = id_
        self.created_at = datetime.strptime(created_at, "%Y-%m-%dT%H:%M:%S.%f%z")
        self.content = content
        self.user_name = user_name


class TicketAssignment:
    id_: int
    assignment_entity_id: int
    assignment_entity_code: str
    entity_id: int

    def __init__(self,  assignment_entity_id: int, entity_id: int, id_: int = 0,
                 assignment_entity_code: str = "") -> None:
        self.id_ = id_
        self.assignment_entity_id = assignment_entity_id
        self.assignment_entity_code = assignment_entity_code
        self.entity_id = entity_id


class Ticket:
    id_: int
    id_num: str
    time_received: datetime
    subject: str
    content: str
    department_id: int
    user_id: int
    priority_id: int
    priority_code: str
    status_id: int
    status_code: str
    source_id: int
    source_code: str
    comments: Optional[List[TicketComment]]
    main_assignment: Optional[TicketAssignment]
    assignments: Optional[List[TicketAssignment]]

    def __init__(self,
                 id_: int,
                 id_num: str,
                 time_received: str,
                 subject: str,
                 content: str,
                 department_id: int,
                 user_id: int,
                 priority: Dict,
                 status: Dict,
                 source: Dict,
                 comments: List[Dict],
                 main_assignment: Dict,
                 assignment: List[Dict]
                 ) -> None:
        self.id_ = id_
        self.id_num = id_num
        try:
            self.time_received = datetime.strptime(time_received, "%Y-%m-%dT%H:%M:%S.%f%z")
        except ValueError:
            self.time_received = datetime.strptime(time_received, "%Y-%m-%dT%H:%M:%S%z")
        self.subject = subject
        self.content = content
        self.department_id = department_id
        self.user_id = user_id
        self.priority_id = priority["id"]
        self.priority_code = priority["code"]
        self.status_id = status["id"]
        self.status_code = status["code"]
        self.source_id = source["id"]
        self.source_code = source["code"]

        self.comments = []
        if comments is not None and len(comments) > 0:
            for tentry in comments:
                try:
                    tcomment = TicketComment(id_=tentry["id"],
                                             created_at=tentry["created_at"],
                                             content=tentry["content"],
                                             user_name=tentry["user_name"])
                    self.comments.append(tcomment)
                except KeyError as e:
                    print(f"Key error: {e.args}")
                    continue

        if main_assignment is not None:
            try:
                tassignment = TicketAssignment(id_=main_assignment["id"],
                                               assignment_entity_id=main_assignment["assignment_entity"]["id"],
                                               assignment_entity_code=main_assignment["assignment_entity"]["code"],
                                               entity_id=main_assignment["entity_id"])
                self.main_assignment = tassignment
            except KeyError as e:
                print(f"Key error: {e.args}")
        else:
            self.main_assignment = None

        # Hinweis: Im JSON lautet dieser Wert "assignment", wir verwenden in der Klasse jedoch "assignments", weil
        # ich das passender finde
        self.assignments = []
        if assignment is not None and len(assignment) > 0:
            for tentry in assignment:
                try:
                    tassignment = TicketAssignment(id_=tentry["id"],
                                                   assignment_entity_id=tentry["assignment_entity"]["id"],
                                                   assignment_entity_code=tentry["assignment_entity"]["code"],
                                                   entity_id=tentry["entity_id"])
                    self.assignments.append(tassignment)
                except KeyError as e:
                    print(f"Key error: {e.args}")


class CommunicationCatalog:
    ticket_assignment_entity_name: Dict
    ticket_priority_name: Dict
    ticket_source_name: Dict
    ticket_status_name: Dict
    ticket_assignment_entity_id: Dict
    ticket_priority_id: Dict
    ticket_source_id: Dict
    ticket_status_id: Dict

    def __init__(self,
                 source_catalogues: List[Dict]
                 ) -> None:
        dicts = []
        dicts_rev = []
        for tcat in source_catalogues:
            tdict = {}
            tdict_rev = {}
            for tentry in tcat:
                tdict[tentry["Id"]] = tentry["Code"]
                tdict_rev[tentry["Code"]] = tentry["Id"]
            dicts.append(tdict)
            dicts_rev.append(tdict_rev)

        self.ticket_assignment_entity_name = dicts[0]
        self.ticket_priority_name = dicts[1]
        self.ticket_source_name = dicts[2]
        self.ticket_status_name = dicts[3]

        self.ticket_assignment_entity_id = dicts_rev[0]
        self.ticket_priority_id = dicts_rev[1]
        self.ticket_source_id = dicts_rev[2]
        self.ticket_status_id = dicts_rev[3]


class ResponsibleOfficial:
    id_: int
    code_short: str
    automatic_mails_activated: bool
    universal_responsibility_possible: bool
    person_id: int
    person_name: str

    def __init__(self, id_: int, code_short: str, automatic_mails_activated: bool,
                 universal_responsibility_possible: bool, person_id: int, person_name: str):
        self.id_ = id_
        self.code_short = code_short
        self.automatic_mails_activated = automatic_mails_activated
        self.universal_responsibility_possible = universal_responsibility_possible
        self.person_id = person_id
        self.person_name = person_name


class JurisdictionListEntry:
    id_: int
    main_jurisdiction: bool
    responsible_official: ResponsibleOfficial
    department_type_id: int
    department_type_name: str

    def __init__(self, id_: int, main_jurisdiction: bool, responsible_official: dict,
                 department_type: dict):
        self.id_ = id_
        self.main_jurisdiction = main_jurisdiction
        responsible_official["id_"] = responsible_official.pop("id")
        self.responsible_official = ResponsibleOfficial(**responsible_official)
        self.department_type_id = department_type.get("id")
        self.department_type_name = department_type.get("name")


class UseUnitJurisdiction:
    use_unit: UseUnitShort
    use_unit_universal_responsibility: bool
    use_unit_universal_responsible_official: Optional[ResponsibleOfficial]
    economic_unit_universal_responsibility: bool
    economic_unit_universal_responsible_official: Optional[ResponsibleOfficial]
    use_unit_jurisdiction_list: List[JurisdictionListEntry]

    def __init__(self, use_unit: dict, use_unit_universal_responsibility: bool,
                 use_unit_universal_responsible_official: dict, economic_unit_universal_responsibility: bool,
                 economic_unit_universal_responsible_official, use_unit_jurisdiction_list: List[Dict]):
        use_unit["id_"] = use_unit.pop("id")
        self.use_unit = UseUnitShort(**use_unit)
        self.use_unit_universal_responsibility = use_unit_universal_responsibility
        if use_unit_universal_responsible_official is not None:
            use_unit_universal_responsible_official["id_"] = use_unit_universal_responsible_official.pop("id")
            self.use_unit_universal_responsible_official = ResponsibleOfficial(
                **use_unit_universal_responsible_official)
        else:
            self.use_unit_universal_responsible_official = None

        self.economic_unit_universal_responsibility = economic_unit_universal_responsibility
        if economic_unit_universal_responsible_official is not None:
            economic_unit_universal_responsible_official["id_"] = economic_unit_universal_responsible_official.pop("id")
            self.economic_unit_universal_responsible_official = ResponsibleOfficial(
                **economic_unit_universal_responsible_official)
        else:
            self.economic_unit_universal_responsible_official = None

        self.use_unit_jurisdiction_list = []
        if use_unit_jurisdiction_list is not None and len(use_unit_jurisdiction_list) > 0:
            for juris_entry in use_unit_jurisdiction_list:
                juris_entry["id_"] = juris_entry.pop("id")
                new_juris_entry = JurisdictionListEntry(**juris_entry)
                self.use_unit_jurisdiction_list.append(new_juris_entry)


class EconomicUnitJurisdiction:
    economic_unit: EconomicUnitShort
    economic_unit_universal_responsibility: bool
    economic_unit_universal_responsible_official: Optional[ResponsibleOfficial]
    economic_unit_jurisdiction_list: List[JurisdictionListEntry]

    def __init__(self, economic_unit: dict, economic_unit_universal_responsibility: bool,
                 economic_unit_universal_responsible_official, economic_unit_jurisdiction_list: List[Dict]):
        economic_unit["id_"] = economic_unit.pop("id")
        self.economic_unit = EconomicUnitShort(**economic_unit)
        self.economic_unit_universal_responsibility = economic_unit_universal_responsibility
        if economic_unit_universal_responsible_official is not None:
            economic_unit_universal_responsible_official["id_"] = economic_unit_universal_responsible_official.pop("id")
            self.economic_unit_universal_responsible_official = ResponsibleOfficial(
                **economic_unit_universal_responsible_official)
        else:
            self.economic_unit_universal_responsible_official = None
        self.economic_unit_jurisdiction_list = []
        if economic_unit_jurisdiction_list is not None and len(economic_unit_jurisdiction_list) > 0:
            for juris_entry in economic_unit_jurisdiction_list:
                juris_entry["id_"] = juris_entry.pop("id")
                new_juris_entry = JurisdictionListEntry(**juris_entry)
                self.economic_unit_jurisdiction_list.append(new_juris_entry)
