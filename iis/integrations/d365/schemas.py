from pydantic import BaseModel

class AccountInput(BaseModel):
    name: str
    industry: str
    owner: str
    relationship_type: str
    category: str
    zip: str

class ContactInput(BaseModel):
    firstname: str
    lastname: str
    email: str
    phone: str
    company: str
    job_title: str

class OpportunityInput(BaseModel):
    name: str
    oppty_potential_customer_name: str
    oppty_primary_contact_email: str
    oppty_owner_email: str
    oppty_partner_email: str
    sales_team: str
    sales_stage: str
    forecast_stage: str
    estimated_close_date: str
    lead_source: str
    lead_source_details: str
    #referring_employee: str

class ProductServiceInput(BaseModel):
    name: str
    product_service: str
    service_type: str
    cost_center: str
    value_based_pricing: str
    engagement_type: str
    opportunity_name: str


class CPIFInput(BaseModel):
    cpif_name: str
    project_start: str
    project_end: str
    total_est_hours: float
    tax_service_india_authorized: bool
    attest_project: bool
    bill_to_customer_number: str
    cal_period01: float
    cal_period02: float
    cal_period03: float
    cal_period04: float
    cal_period05: float
    cal_period06: float
    cal_period07: float
    cal_period08: float
    cal_period09: float
    cal_period10: float
    cal_period11: float
    cal_period12: float
    contract_amt: float
    contract_type: str
    customer_po: str
    el_signed: bool
    expected_margin: int
    account_name: str
    opportunity_name: str
    project_hierarchy: str
    project_template: str
    spm_template: str
    rate_sheet: str
    secretary_of_state: str
    spm_template: str
    armanino_company: str
    workday_contract_company: str
    service_code: str
    owner_email: str
    project_manager_email: str
    asst_projectmanager_email: str
    customer_collection_lead_email: str
    billing_manager_email: str
    project_delivery_lead_email: str
    invoice_type: str  # Local Choice
    xcm_tax_form: str  # Local Choice
    sync_to_xcm: bool
    sent_to_xcm: bool
    go_systems: bool
    sent_to_go_systems: bool
    status_code: str  # Local Choice

class BatchInput(BaseModel):
    account: AccountInput
    contact: ContactInput
    opportunity: OpportunityInput
    product_service: ProductServiceInput

class DeepInsertInput(BaseModel):
    account: AccountInput
    contact: ContactInput
    opportunity: OpportunityInput
    product_service: ProductServiceInput
