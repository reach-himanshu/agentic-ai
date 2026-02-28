from typing import Optional, Dict, Any, List
from core.base_client import BaseHttpClient
from .config import d365_settings
from .auth import D365Auth
from .schemas import DeepInsertInput, AccountInput, ContactInput, OpportunityInput, ProductServiceInput, CPIFInput
from .schemas import DeepInsertInput, AccountInput, ContactInput, OpportunityInput, ProductServiceInput, CPIFInput
from .metadata import option_set_service, lookup_service
from rapidfuzz import fuzz
from fastapi import HTTPException
import logging
import urllib.parse

logger = logging.getLogger(__name__)

def sanitize_log_input(value: str) -> str:
    """Sanitize user input for safe logging to prevent log injection attacks."""
    if not value:
        return ""
    # Remove newlines and carriage returns to prevent log injection
    return str(value).replace('\n', ' ').replace('\r', ' ').replace('\x00', '')[:200]

class D365Client(BaseHttpClient):
    def __init__(self, verify: bool = None, resource_url: Optional[str] = None, tenant_id: Optional[str] = None):
        if verify is None:
            verify = d365_settings.SSL_VERIFY
            
        super().__init__(
            base_url=resource_url or d365_settings.D365_RESOURCE_URL,
            auth=D365Auth(verify=verify, resource_url=resource_url, tenant_id=tenant_id),
            verify=verify
        )

    async def get_accounts(self):
        """
        Fetch top 5 accounts from D365 with basic fields.
        Returns the list of accounts found in the 'value' key of the OData response.
        """
        # Select basic fields and limit to top 5
        query_params = {
            "$select": "name,accountnumber,telephone1,emailaddress1,address1_city",
            "$top": 5
        }
        response = await self.get("/api/data/v9.2/accounts", params=query_params)
        
        # D365 OData responses wrap the list of items in a "value" key
        if isinstance(response, dict) and "value" in response:
            return response["value"]
        return response

    async def search_accounts(self, query: str, top: int = 5) -> List[Dict[str, Any]]:
        """
        Search for accounts by name using OData filter.
        """
        safe_query = urllib.parse.quote(query.replace("'", "''"))
        url = f"/api/data/v9.2/accounts?$select=name,accountnumber,telephone1,emailaddress1&$filter=contains(name,'{safe_query}')&$top={top}"
        response = await self.get(url)
        if isinstance(response, dict) and "value" in response:
            return response["value"]
        return []

    async def get_opportunities(self, top: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch recent opportunities from D365.
        """
        query_params = {
            "$select": "name,estimatedvalue,estimatedclosedate,statuscode",
            "$top": top,
            "$orderby": "createdon desc"
        }
        response = await self.get("/api/data/v9.2/opportunities", params=query_params)
        if isinstance(response, dict) and "value" in response:
            return response["value"]
        return []

    async def resolve_lookup(self, entity: str, search_field: str, value: str) -> str:
        """
        Fuzzy lookup for an entity ID.
        """
        if not value:
            raise HTTPException(status_code=400, detail=f"Lookup value for {entity}.{search_field} cannot be empty.")
            
        # Determine ID field name (convention: entity minus 's' + 'id', usually)
        # But D365 is inconsistent. e.g. 'accounts' -> 'accountid'.
        # Using simple heuristic from reference: entity[:-1] + "id"
        # Reference: res[f"{entity[:-1]}id"]
        entity_id_field = f"{entity[:-1]}id"
        
        # URL encode the value for filter
        safe_value = urllib.parse.quote(value.replace("'", "''"))

        url = f"/api/data/v9.2/{entity}?$select={search_field},{entity_id_field}&$filter=contains({search_field},'{safe_value}')"
        
        response = await self.get(url)
        results = response.get("value", []) if isinstance(response, dict) else []
        
        best_match = None
        best_score = 0
        
        for res in results:
            res_val = res.get(search_field, "")
            if not res_val:
                continue
                
            score = fuzz.token_sort_ratio(value.lower(), res_val.lower())
            if score > best_score:
                best_score = score
                best_match = res
        
        if best_match and best_score >= 85:
            logger.info(f"Resolved lookup {sanitize_log_input(entity)}.{sanitize_log_input(search_field)} to match (Score: {best_score})")
            return best_match[entity_id_field]
            
        logger.warning(f"Lookup failed in {sanitize_log_input(entity)} (Best score: {best_score})")
        raise HTTPException(status_code=404, detail=f"Lookup value '{value}' not found in {entity}")

    async def resolve_lookup_specific(self, entity: str, entity_id_field: str, search_field: str, value: str) -> str:
        """
        Fuzzy lookup with specific ID field name.
        """
        if not value:
            raise HTTPException(status_code=400, detail=f"Lookup value for {entity}.{search_field} cannot be empty.")
            
        safe_value = urllib.parse.quote(value.replace("'", "''"))
        url = f"/api/data/v9.2/{entity}?$select={search_field},{entity_id_field}&$filter=contains({search_field},'{safe_value}')"
        
        response = await self.get(url)
        results = response.get("value", []) if isinstance(response, dict) else []
        
        best_match = None
        best_score = 0
        
        for res in results:
            res_val = res.get(search_field, "")
            if not res_val:
                continue

            score = fuzz.token_sort_ratio(value.lower(), res_val.lower())
            if score > best_score:
                best_score = score
                best_match = res
                
        if best_match and best_score >= 85:
            logger.info(f"Resolved lookup (Score: {best_score})")
            return best_match[entity_id_field]

        raise HTTPException(status_code=404, detail=f"Lookup value '{value}' not found in {entity}")

    async def create_deep_insert(self, data: DeepInsertInput):
        """
        Creates Account, Contact, Opportunity, and Product/Service in a single transaction.
        """
        # Ensure metadata is loaded
        if not option_set_service._loaded:
            await option_set_service.load(self)

        # Build payload asynchronously
        payload = await self._build_deep_insert_payload(data)
        
        logger.info(f"Sending Deep Insert Payload for account")
        
        # Deep insert usually targets the primary entity, here 'accounts'
        response = await self.post("/api/data/v9.2/accounts", json=payload, headers={"Prefer": "return=representation"})
        
        if isinstance(response, dict) and "error" in response:
             raise HTTPException(status_code=500, detail=response["error"])
             
        return response

    async def _build_deep_insert_payload(self, data: DeepInsertInput) -> Dict[str, Any]:
        # 1. Resolve Option Sets (Sync)
        # Using safe resolve with fallbacks or errors would be better, but strict per reference
        def resolve_os(field, entity, val):
            res = option_set_service.resolve(field, val)
            if res is None:
                raise HTTPException(status_code=400, detail=f"Invalid option '{val}' for {field}")
            return res

        industry_code = resolve_os("Industry", "account", data.account.industry)
        relationship_code = resolve_os("Relationship_Type", "account", data.account.relationship_type)
        category_code = resolve_os("Category", "account", data.account.category)
        
        sales_team_code = resolve_os("Sales_Team", "opportunity", data.opportunity.sales_team)
        sales_stage_code = resolve_os("Sales_Stage", "opportunity", data.opportunity.sales_stage)
        forecast_stage_code = resolve_os("Forecast_Stage", "opportunity", data.opportunity.forecast_stage)
        lead_source_code = resolve_os("Lead_Source", "opportunity", data.opportunity.lead_source)
        # lead_source_detail_code = resolve_os("Lead_Source_Detail", "opportunity", data.opportunity.lead_source_details) # Optional?
        # Reference had it.
        lead_source_detail_code = resolve_os("Lead_Source_Detail", "opportunity", data.opportunity.lead_source_details)

        value_based_pricing_val = resolve_os("Value_Based_Pricing", "am_productsandservices", data.product_service.value_based_pricing)
        engagement_type_val = resolve_os("P_S_Engagement_Type", "am_productsandservices", data.product_service.engagement_type)
        product_service_val = resolve_os("Product_Service", "am_productsandservices", data.product_service.product_service)

        # 2. Resolve Lookups (Async)
        cost_center_id = await self.resolve_lookup("am_costcenters", "am_costcentername", data.product_service.cost_center)
        service_code_id = await self.resolve_lookup_specific("am_armservicecodeses", "am_armservicecodesid", "am_name", data.product_service.service_type)
        
        owner_id = await self.resolve_lookup('systemusers', 'domainname', data.opportunity.oppty_owner_email)
        partner_id = await self.resolve_lookup('systemusers', 'domainname', data.opportunity.oppty_partner_email)

        # 3. Construct Payload
        # Note: Relation names like 'opportunity_customer_accounts' must be exact.
        # Assuming reference was correct.
        
        return {
            "name": data.account.name,
            "new_industry": industry_code,
            "customertypecode": relationship_code,
            "accountcategorycode": category_code,
            "address1_postalcode": data.account.zip,
            "primarycontactid": {
                "firstname": data.contact.firstname,
                "lastname": data.contact.lastname,
                "emailaddress1": data.contact.email,
                "telephone1": data.contact.phone,
                "jobtitle": data.contact.job_title
            },
            "opportunity_customer_accounts": [
                {
                    "name": data.opportunity.name,
                    "am_salesteam": sales_team_code,
                    "salesstagecode": sales_stage_code,
                    "new_opptypartnerid@odata.bind": f"/systemusers({partner_id})",
                    "ownerid@odata.bind": f"/systemusers({owner_id})",
                    "am_forecaststage": forecast_stage_code,
                    "estimatedclosedate": data.opportunity.estimated_close_date,
                    "am_leadsourceglobal": lead_source_code,
                    "am_leadsourcedetailglobal": lead_source_detail_code,
                    "am_opportunity_am_productsandservices": [
                        {
                            "am_name": data.product_service.name,
                            "am_valuebasedpricing": value_based_pricing_val,
                            "am_productserviceengagementtype": engagement_type_val,
                            "am_productservice": product_service_val,
                            "am_ServiceType@odata.bind": f"/am_armservicecodeses({service_code_id})",
                            "am_CostCenter@odata.bind": f"/am_costcenters({cost_center_id})"
                        }
                    ]
                }
            ]
        }

    async def create_account(self, data: AccountInput) -> Dict[str, Any]:
        """Creates an account in D365."""
        if not option_set_service._loaded:
            await option_set_service.load(self)
            
        industry_code = option_set_service.resolve("Industry", data.industry)
        relationship_code = option_set_service.resolve("Relationship_Type", data.relationship_type)
        category_code = option_set_service.resolve("Category", data.category)
        
        payload = {
            "name": data.name,
            "new_industry": industry_code,
            "customertypecode": relationship_code,
            "accountcategorycode": category_code,
            "address1_postalcode": data.zip
        }
        
        logger.info(f"Creating Account")
        response = await self.post("/api/data/v9.2/accounts", json=payload, headers={"Prefer": "return=representation"})
        return response

    async def create_contact(self, data: ContactInput) -> Dict[str, Any]:
        """Creates a contact in D365."""
        account_id = await self.resolve_lookup("accounts", "name", data.company)
        
        payload = {
            "firstname": data.firstname,
            "lastname": data.lastname,
            "emailaddress1": data.email,
            "telephone1": data.phone,
            "jobtitle": data.job_title,
            "parentcustomerid_account@odata.bind": f"/accounts({account_id})"
        }
        
        logger.info("Creating Contact")
        response = await self.post("/api/data/v9.2/contacts", json=payload, headers={"Prefer": "return=representation"})
        return response

    async def create_opportunity(self, data: OpportunityInput) -> Dict[str, Any]:
        """Creates an opportunity in D365."""
        if not option_set_service._loaded:
            await option_set_service.load(self)

        potential_customer_id = await self.resolve_lookup("accounts", "name", data.oppty_potential_customer_name)
        
        # Lookups/OptionSets
        payload = {
            "name": data.name,
            "customerid_account@odata.bind": f"/accounts({potential_customer_id})",
            "am_salesteam": option_set_service.resolve("Sales_Team", data.sales_team),
            "salesstagecode": option_set_service.resolve("Sales_Stage", data.sales_stage),
            "am_forecaststage": option_set_service.resolve("Forecast_Stage", data.forecast_stage),
            "estimatedclosedate": data.estimated_close_date,
            "am_leadsourceglobal": option_set_service.resolve("Lead_Source", data.lead_source),
        }
        
        # Optional relationships
        if data.oppty_primary_contact_email:
            try:
                contact_id = await self.resolve_lookup('contacts', 'emailaddress1', data.oppty_primary_contact_email)
                payload["new_primarycontactid@odata.bind"] = f"/contacts({contact_id})"
            except HTTPException:
                logger.warning("Contact not found, skipping link.")

        if data.oppty_owner_email:
            owner_id = await self.resolve_lookup('systemusers', 'domainname', data.oppty_owner_email)
            payload["ownerid@odata.bind"] = f"/systemusers({owner_id})"

        if data.oppty_partner_email:
             # Assuming partner is also a systemuser based on reference
            partner_id = await self.resolve_lookup('systemusers', 'domainname', data.oppty_partner_email)
            payload["new_opptypartnerid@odata.bind"] = f"/systemusers({partner_id})"
            
        logger.info("Creating Opportunity")
        response = await self.post("/api/data/v9.2/opportunities", json=payload, headers={"Prefer": "return=representation"})
        return response

    async def create_product_service(self, data: ProductServiceInput) -> Dict[str, Any]:
        """Creates a Product/Service record."""
        if not option_set_service._loaded:
            await option_set_service.load(self)
            
        opportunity_id = await self.resolve_lookup_specific("opportunities", "opportunityid", "name", data.opportunity_name)
        cost_center_id = await self.resolve_lookup("am_costcenters", "am_costcentername", data.cost_center)
        service_code_id = await self.resolve_lookup_specific("am_armservicecodeses", "am_armservicecodesid", "am_name", data.service_type)

        payload = {
            "am_name": data.name,
            "am_valuebasedpricing": option_set_service.resolve("Value_Based_Pricing", data.value_based_pricing),
            "am_productserviceengagementtype": option_set_service.resolve("P_S_Engagement_Type", data.engagement_type),
            "am_productservice": option_set_service.resolve("Product_Service", data.product_service),
            "am_opportunityid@odata.bind": f"/opportunities({opportunity_id})",
            "am_ServiceType@odata.bind": f"/am_armservicecodeses({service_code_id})",
            "am_CostCenter@odata.bind": f"/am_costcenters({cost_center_id})"
        }

        logger.info("Creating Product/Service")
        response = await self.post("/api/data/v9.2/am_productsandserviceses", json=payload, headers={"Prefer": "return=representation"})
        return response

    async def create_cpif(self, data: CPIFInput) -> Dict[str, Any]:
        """Creates a CPIF record."""
        # Resolve lookups (parallelize where possible, but keeping simple for now)
        lookups = {}
        # Simple/Safe lookups
        lookups["am_account"] = await self.resolve_lookup("accounts", "name", data.account_name)
        lookups["am_cpifcontracttype"] = await self.resolve_lookup("am_contracttypes", "am_name", data.contract_type)
        lookups["am_opportunity"] = await self.resolve_lookup_specific("opportunities", "opportunityid", "name", data.opportunity_name)
        lookups["am_projectmanager"] = await self.resolve_lookup("systemusers", "domainname", data.project_manager_email)
        lookups["am_asstprojectmanager"] = await self.resolve_lookup("systemusers", "domainname", data.asst_projectmanager_email)
        lookups["am_customercollectionlead"] = await self.resolve_lookup("systemusers", "domainname", data.customer_collection_lead_email)
        lookups["am_billingmanager"] = await self.resolve_lookup("systemusers", "domainname", data.billing_manager_email)
        lookups["am_resource"] = await self.resolve_lookup("systemusers", "domainname", data.project_delivery_lead_email)
        lookups["am_projecthierarchyid"] = await self.resolve_lookup_specific("am_projecthierarchies", "am_projecthierarchyid", "am_name", data.project_hierarchy)
        lookups["am_projecttemplateid"] = await self.resolve_lookup("am_projecttemplates", "am_name", data.project_template)
        lookups["am_ratesheet"] = await self.resolve_lookup("am_ratesheets", "am_name", data.rate_sheet)
        lookups["am_secretaryofstate"] = await self.resolve_lookup("am_secretaryofstates", "am_name", data.secretary_of_state)
        lookups["am_servicecode"] = await self.resolve_lookup_specific("am_armservicecodeses", "am_armservicecodesid", "am_name", data.service_code)
        lookups["am_spmtemplate"] = await self.resolve_lookup("am_spmtemplates", "am_name", data.spm_template)
        lookups["am_workdaycontractcompany"] = await self.resolve_lookup_specific("am_workdaycompanies", "am_workdaycompanyid", "am_name", data.workday_contract_company)

        # Option Sets
        if not option_set_service._loaded:
            await option_set_service.load(self)

        payload = {
            "am_name": data.cpif_name,
            "am_account@odata.bind": f"/accounts({lookups['am_account']})",
            "am_asstprojectmanager@odata.bind": f"/systemusers({lookups['am_asstprojectmanager']})",
            "am_cpifcontracttype@odata.bind": f"/am_contracttypes({lookups['am_cpifcontracttype']})",
            "am_customercollectionlead@odata.bind": f"/systemusers({lookups['am_customercollectionlead']})",
            "am_opportunity@odata.bind": f"/opportunities({lookups['am_opportunity']})",
            "am_billingmanager@odata.bind": f"/systemusers({lookups['am_billingmanager']})",
            "am_resource@odata.bind": f"/systemusers({lookups['am_resource']})",
            "am_projecthierarchyid@odata.bind": f"/am_projecthierarchies({lookups['am_projecthierarchyid']})",
            "am_projectmanager@odata.bind": f"/systemusers({lookups['am_projectmanager']})",
            "am_projecttemplateid@odata.bind": f"/am_projecttemplates({lookups['am_projecttemplateid']})",
            "am_ratesheet@odata.bind": f"/am_ratesheets({lookups['am_ratesheet']})",
            "am_secretaryofstate@odata.bind": f"/am_secretaryofstates({lookups['am_secretaryofstate']})",
            "am_servicecode@odata.bind": f"/am_servicetypes({lookups['am_servicecode']})",
            "am_spmtemplate@odata.bind": f"/am_spmtemplates({lookups['am_spmtemplate']})",
            "am_workdaycontractcompany@odata.bind": f"/am_workdaycontractcompanies({lookups['am_workdaycontractcompany']})",
            
            "am_invoicetypeid": option_set_service.resolve("Invoice_Type", data.invoice_type),
            "statuscode": option_set_service.resolve("Status_Reason", data.status_code),
            "am_xcmtaxform": option_set_service.resolve("XCM_Tax_Form", data.xcm_tax_form),
            
            "am_authorized": 1 if data.tax_service_india_authorized else 0,
            "am_attestproject": 1 if data.attest_project else 0,
            "am_billtocustomernameorcus": data.bill_to_customer_number,
            "am_calcperiodval01": data.cal_period01,
            "am_contractamount": data.contract_amt,
            "am_customerpo": data.customer_po,
            "am_elsigned": 1 if data.el_signed else 0,
            "am_expectedmargin": data.expected_margin,
            "am_senttogosystems": 1 if data.sent_to_go_systems else 0,
            "am_senttoxcm": 1 if data.sent_to_xcm else 0,
            "am_gosystemsaccount": 1 if data.go_systems else 0
        }

        logger.info("Creating CPIF")
        return response

    async def get_option_sets(self) -> Dict[str, Dict[int, str]]:
        """Returns all cached option sets, ensuring they are loaded."""
        if not option_set_service._loaded:
            await option_set_service.load(self)
        return option_set_service.get_all()

    async def get_option_set_by_field(self, field_name: str) -> Dict[int, str]:
        """Returns options for a specific field name."""
        if not option_set_service._loaded:
            await option_set_service.load(self)
        
        cache = option_set_service.get_all()
        if field_name not in cache:
            raise HTTPException(status_code=404, detail=f"Option set '{field_name}' not found")
        return cache[field_name]

    async def get_lookups(self) -> Dict[str, List[Dict[str, Any]]]:
        """Returns all cached lookups, ensuring they are loaded."""
        if not lookup_service._loaded:
            await lookup_service.load(self)
        return lookup_service.get_all()

    async def get_lookup_by_name(self, name: str) -> List[Dict[str, Any]]:
        """Returns lookup list for a specific display name."""
        if not lookup_service._loaded:
            await lookup_service.load(self)
        
        cache = lookup_service.get_all()
        if name not in cache:
            raise HTTPException(status_code=404, detail=f"Lookup '{name}' not found")
        return cache[name]
