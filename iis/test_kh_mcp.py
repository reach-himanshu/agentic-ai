import sys
import os
import asyncio
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO)

async def test():
    print("--- Knowledge Hub MCP Diagnostic ---")
    sys.path.append(os.getcwd())
    
    try:
        print("1. Testing MCP Registry Import...")
        from mcp_registry.knowledge_hub import mcp as kh_mcp
        print(f" - MCP '{kh_mcp.name}' imported successfully.")
        
        print("\n2. Listing Tools in Knowledge Hub MCP...")
        tools = await kh_mcp.list_tools()
        print(f" - Found {len(tools)} tools:")
        for t in tools:
            print(f"   * {t.name}: {t.description}")
            
        print("\n3. Testing ExecutorAgent Integration...")
        from agents.executor import ExecutorAgent
        executor = ExecutorAgent()
        await executor.initialize_tools()
        print(f" - Executor initialized with {len(executor.tools)} total tools.")
        
        kh_tools = [t for t in executor.tools if t.name.startswith("kb_")]
        print(f" - Knowledge Hub specific tools found in Executor: {len(kh_tools)}")
        for t in kh_tools:
            print(f"   * {t.name}")
            
    except Exception as e:
        print(f"\n[ERROR] Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
