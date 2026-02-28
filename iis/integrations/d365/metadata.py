import logging
from typing import Dict, Any, List, Optional
import asyncio

logger = logging.getLogger(__name__)

def sanitize_log_input(value: str) -> str:
    """Sanitize user input for safe logging to prevent log injection attacks."""
    if not value:
        return ""
    return str(value).replace('\n', ' ').replace('\r', ' ').replace('\x00', '')[:100]

ATTRIBUTES = [
    {"display_name": "Ownership", "logical_name": "ownershipcode", "type": "local", "entity": "account", "metadata": None},
    {"display_name": "Relationship_Type", "logical_name": "customertypecode", "type": "local", "entity": "account", "metadata": None},
    {"display_name": "Category", "logical_name": "accountcategorycode", "type": "local", "entity": "account", "metadata": None},
    {"display_name": "Industry", "logical_name": "new_industry", "type": "global"},
    {"display_name": "Lead_Source_Detail", "logical_name": "am_leadsourcedetail", "type": "global"},
    {"display_name": "Lead_Source", "logical_name": "am_leadsource", "type": "global"},
    {"display_name": "Lead_Source (Software Partner)", "logical_name": "am_leadsourcesoftwarepartner", "type": "global"},
    {"display_name": "Job_Level", "logical_name": "am_opjoblevel", "type": "global"},
    {"display_name": "Job_Function (New)", "logical_name": "am_opjobfunction", "type": "global"},
    {"display_name": "Invoice_Type", "logical_name": "am_invoicetype", "type": "global"},
    {"display_name": "XCM_Tax_Form", "logical_name": "am_xcmtaxform", "type": "local", "entity": "am_deliveryinitiationform", "metadata": None},
    {"display_name": "Forecast_category", "logical_name": "msdyn_forecastcategory", "type": "local", "entity": "opportunity", "metadata": None},
    {"display_name": "Sales_Stage", "logical_name": "salesstagecode", "type": "local", "entity": "opportunity", "metadata": None},
    {"display_name": "Entity_Count", "logical_name": "am_entitycount", "type": "global"},
    {"display_name": "Forecast_Stage", "logical_name": "am_forecaststageos", "type": "global"},
    {"display_name": "Sales_Team", "logical_name": "am_salesteam", "type": "global"},
    {"display_name": "Stage_0_Lose_Reason", "logical_name": "am_stage0lostreasons", "type": "global"},
    {"display_name": "Oppty_Status", "logical_name": "am_opptystatus", "type": "local", "entity": "am_productsandservices", "metadata": None},
    {"display_name": "P_S_Engagement_Type", "logical_name": "am_productserviceengagementtype", "type": "local", "entity": "am_productsandservices", "metadata": None},
    {"display_name": "Product_Service", "logical_name": "am_productservice", "type": "local", "entity": "am_productsandservices", "metadata": None},
    {"display_name": "Team", "logical_name": "am_team", "type": "global"},
    {"display_name": "Value_Based_Pricing", "logical_name": "am_yesno", "type": "global"},
    {"display_name": "Status_Reason", "logical_name": "statuscode", "type": "local", "entity": "am_deliveryinitiationform", "metadata": "Microsoft.Dynamics.CRM.StatusAttributeMetadata"}
]

import datetime

class OptionSetService:
    def __init__(self):
        # Maps Display Name -> { Label (lower) -> Value (int) }
        self._cache: Dict[str, Dict[str, int]] = {}
        self._original_cache: Dict[str, Dict[int, str]] = {} # Value -> Label
        self._loaded = False
        self.last_loaded_at: Optional[datetime.datetime] = None
        self.load_count: int = 0

    async def load(self, client: Any):
        """
        Loads option sets from D365 using the provided client.
        Client must be an instance of D365Client (duck-typed for async get).
        """
        logger.info("Loading D365 Option Sets...")
        
        for attr in ATTRIBUTES:
            key = attr["display_name"]
            try:
                metadata = ""
                if attr["type"] == "global":
                    url = f"/api/data/v9.2/GlobalOptionSetDefinitions(Name='{attr['logical_name']}')"
                else:
                    if attr["metadata"] is not None and attr["metadata"] == "Microsoft.Dynamics.CRM.StatusAttributeMetadata":
                        metadata = attr["metadata"]
                    else:
                        metadata = "Microsoft.Dynamics.CRM.PicklistAttributeMetadata"
                    url = f"/api/data/v9.2/EntityDefinitions(LogicalName='{attr['entity']}')/Attributes(LogicalName='{attr['logical_name']}')/{metadata}?$select=LogicalName&$expand=OptionSet,GlobalOptionSet"

                response = await client.get(url)
                
                # Handling response which might be dict or parsed JSON
                data = response if isinstance(response, dict) else {} # Assuming client.get returns dict

                options = []
                if "OptionSet" in data:
                    options = data["OptionSet"].get("Options", [])
                elif "GlobalOptionSet" in data:
                    options = data["GlobalOptionSet"].get("Options", [])
                elif "Options" in data:
                    options = data.get("Options", [])

                # Build caches
                # Original: Value(int) -> Label(Display)
                original_map = {
                    opt["Value"]: opt["Label"]["UserLocalizedLabel"]["Label"]
                    for opt in options if "UserLocalizedLabel" in opt["Label"]
                }
                self._original_cache[key] = original_map

                # Reverse: Label(lower) -> Value(int)
                reverse_map = {
                    label.lower(): value
                    for value, label in original_map.items()
                }
                self._cache[key] = reverse_map
                
            except Exception as e:
                logger.error(f"Failed to load option set {key}: {e}")
                
        self._loaded = True
        self.last_loaded_at = datetime.datetime.now()
        self.load_count += 1
        logger.info(f"Loaded {len(self._cache)} option sets. (Count: {self.load_count})")

    def resolve(self, field_display_name: str, label: str) -> Optional[int]:
        """
        Resolves a label (case-insensitive) to its integer value for a given field.
        """
        if not label:
            return None
            
        field_map = self._cache.get(field_display_name)
        if not field_map:
            logger.warning(f"Option set field not found in cache.")
            return None
            
        value = field_map.get(label.lower())
        if value is None:
            logger.warning(f"Label not found in option set.")
            return None
            
        return value

    def get_all(self):
        return self._original_cache

    def get_stats(self) -> Dict[str, Any]:
        return {
            "loaded": self._loaded,
            "count": len(self._cache),
            "last_updated": self.last_loaded_at,
            "loads_performed": self.load_count
        }


LOOKUPS = [
  {
    "display_name": "Cost Centers",
    "entity": "am_costcenters",
    "id_field": "am_costcenterid",
    "name_field": "am_costcentername"
  },
  {
    "display_name": "Service Types",
    "entity": "am_armservicecodeses",
    "id_field": "am_armservicecodesid",
    "name_field": "am_name"
  },
  {
    "display_name": "Contract Types",
    "entity": "am_contracttypes",
    "id_field": "am_contracttypesid",
    "name_field": "am_name"
  },
  {
    "display_name": "Project Templates",
    "entity": "am_projecttemplates",
    "id_field": "am_projecttemplatesid",
    "name_field": "am_name"
  },
  {
    "display_name": "Rate Sheets",
    "entity": "am_ratesheets",
    "id_field": "am_ratesheetsid",
    "name_field": "am_name"
  },
   {
    "display_name": "Secretary of States",
    "entity": "am_secretaryofstates",
    "id_field": "am_secretaryofstatesid",
    "name_field": "am_name"
  },
  {
    "display_name": "SPM Templates",
    "entity": "am_spmtemplates",
    "id_field": "am_spmtemplatesid",
    "name_field": "am_name"
  },
  {
    "display_name": "Workday Companies",
    "entity": "am_workdaycompanies",
    "id_field": "am_workdaycompanyid",
    "name_field": "am_name"
  }
]

class LookupService:
    def __init__(self):
        # Maps Display Name -> List[Dict]
        self._cache: Dict[str, List[Dict[str, Any]]] = {}
        self._loaded = False
        self.last_loaded_at: Optional[datetime.datetime] = None
        self.load_count: int = 0

    async def load(self, client: Any):
        """
        Loads lookup data from D365 using the provided client.
        """
        logger.info("Loading D365 Lookups...")
        
        for item in LOOKUPS:
            key = item["display_name"]
            entity = item["entity"]
            id_field = item["id_field"]
            name_field = item["name_field"]
            
            try:
                # Fetch only ID and Name
                url = f"/api/data/v9.2/{entity}?$select={id_field},{name_field}"
                # Add status filter if applicable (optional, not strictly requested but good practice)
                # url += "&$filter=statecode eq 0" 
                
                response = await client.get(url)
                
                start_time = datetime.datetime.now()
                data = response.get("value", []) if isinstance(response, dict) else []
                
                processed_list = []
                for record in data:
                    processed_list.append({
                        "id": record.get(id_field),
                        "name": record.get(name_field),
                        "original_record": record # Keep original just in case
                    })
                
                self._cache[key] = processed_list
                
            except Exception as e:
                logger.error(f"Failed to load lookup {key}: {e}")
                
        self._loaded = True
        self.last_loaded_at = datetime.datetime.now()
        self.load_count += 1
        logger.info(f"Loaded {len(self._cache)} lookup lists. (Count: {self.load_count})")

    def get_all(self):
        return self._cache

    def get_by_name(self, name: str) -> Optional[List[Dict[str, Any]]]:
        return self._cache.get(name)

    def get_stats(self) -> Dict[str, Any]:
        return {
            "loaded": self._loaded,
            "count": len(self._cache),
            "last_updated": self.last_loaded_at,
            "loads_performed": self.load_count
        }

# Global instances
option_set_service = OptionSetService()
lookup_service = LookupService()
