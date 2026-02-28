from fastapi import APIRouter, HTTPException
from .service import D365Client
from .schemas import DeepInsertInput, AccountInput, ContactInput, OpportunityInput, ProductServiceInput, CPIFInput

router = APIRouter()

@router.get("/accounts")
async def get_d365_accounts():
    try:
        async with D365Client() as client:
            return await client.get_accounts()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=repr(e))

@router.get("/resolve-lookup")
async def resolve_lookup(entity: str, search_field: str, value: str):
    try:
        async with D365Client() as client:
            return await client.resolve_lookup(entity, search_field, value)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=repr(e))

@router.get("/resolve-lookup/specific")
async def resolve_lookup_specific(entity: str, entity_id_field: str, search_field: str, value: str):
    try:
        async with D365Client() as client:
            return await client.resolve_lookup_specific(entity, entity_id_field, search_field, value)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=repr(e))

@router.post("/deep-insert")
async def create_deep_insert(data: DeepInsertInput):
    try:
        async with D365Client() as client:
            return await client.create_deep_insert(data)
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=repr(e))

@router.post("/accounts")
async def create_account(data: AccountInput):
    try:
        async with D365Client() as client:
            return await client.create_account(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=repr(e))

@router.post("/contacts")
async def create_contact(data: ContactInput):
    try:
        async with D365Client() as client:
            return await client.create_contact(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=repr(e))

@router.post("/opportunities")
async def create_opportunity(data: OpportunityInput):
    try:
        async with D365Client() as client:
            return await client.create_opportunity(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=repr(e))

@router.post("/products-services")
async def create_product_service(data: ProductServiceInput):
    try:
        async with D365Client() as client:
            return await client.create_product_service(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=repr(e))

@router.post("/cpif")
async def create_cpif(data: CPIFInput):
    try:
        async with D365Client() as client:
            return await client.create_cpif(data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=repr(e))

from .metadata import option_set_service

@router.get("/optionsets")
async def get_option_sets():
    """Returns all cached option sets."""
    try:
        async with D365Client() as client:
            return await client.get_option_sets()
    except Exception as e:
        raise HTTPException(status_code=500, detail=repr(e))

@router.get("/optionsets/stats")
async def get_option_set_stats():
    """Returns metadata about the option set cache."""
    return option_set_service.get_stats()

@router.get("/optionsets/{field_name}")
async def get_option_set_by_field(field_name: str):
    """Returns options for a specific field name (e.g., 'Industry')."""
    try:
        async with D365Client() as client:
            return await client.get_option_set_by_field(field_name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=repr(e))


@router.get("/lookups")
async def get_lookups():
    """Returns all cached lookups."""
    try:
        async with D365Client() as client:
            return await client.get_lookups()
    except Exception as e:
        raise HTTPException(status_code=500, detail=repr(e))

from .metadata import lookup_service

@router.get("/lookups/stats")
async def get_lookup_stats():
    """Returns metadata about the lookup cache."""
    return lookup_service.get_stats()

@router.get("/lookups/{name}")
async def get_lookup_by_name(name: str):
    """Returns lookup list for a specific display name (e.g., 'Cost Centers')."""
    try:
        async with D365Client() as client:
            return await client.get_lookup_by_name(name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=repr(e))

