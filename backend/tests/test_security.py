"""
Security verification tests for role-based access control.
"""
import asyncio
import httpx

BASE_URL = "http://localhost:8000"

# Mock tokens matching backend auth
TOKENS = {
    "admin": "mock-admin-token",
    "sales": "mock-sales-token",
    "viewer": "mock-viewer-token",
}


async def test_security():
    print("=" * 60)
    print("Security Verification Tests")
    print("=" * 60)
    
    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        
        # Test 1: Admin can lookup client
        print("\n[Test 1] Admin - Client Lookup")
        r = await client.get("/api/v1/clients/acme-corp", headers={"Authorization": f"Bearer {TOKENS['admin']}"})
        print(f"  Status: {r.status_code} (expected 200)")
        print(f"  Result: {'PASS' if r.status_code == 200 else 'FAIL'}")
        
        # Test 2: Admin can access team members (Admin-only)
        print("\n[Test 2] Admin - Team Members (Admin-only)")
        r = await client.get("/api/v1/team-members", headers={"Authorization": f"Bearer {TOKENS['admin']}"})
        print(f"  Status: {r.status_code} (expected 200)")
        print(f"  Result: {'PASS' if r.status_code == 200 else 'FAIL'}")
        
        # Test 3: Sales user blocked from assign_owner
        print("\n[Test 3] Sales - Assign Owner (should be 403)")
        r = await client.put(
            "/api/v1/clients/acme-corp/owner",
            headers={"Authorization": f"Bearer {TOKENS['sales']}"},
            json={"new_owner_id": "user-002", "new_owner_name": "Sarah Wilson"},
        )
        print(f"  Status: {r.status_code} (expected 403)")
        print(f"  Result: {'PASS' if r.status_code == 403 else 'FAIL'}")
        
        # Test 4: Viewer blocked from team members
        print("\n[Test 4] Viewer - Team Members (should be 403)")
        r = await client.get("/api/v1/team-members", headers={"Authorization": f"Bearer {TOKENS['viewer']}"})
        print(f"  Status: {r.status_code} (expected 403)")
        print(f"  Result: {'PASS' if r.status_code == 403 else 'FAIL'}")
        
        # Test 5: Unauthenticated request
        print("\n[Test 5] No Auth - Client Lookup (should be 401)")
        r = await client.get("/api/v1/clients/acme-corp")
        print(f"  Status: {r.status_code} (expected 401)")
        print(f"  Result: {'PASS' if r.status_code == 401 else 'FAIL'}")
        
        print("\n" + "=" * 60)
        print("Security Verification Complete")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_security())
