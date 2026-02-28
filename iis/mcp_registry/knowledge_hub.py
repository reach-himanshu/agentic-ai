from mcp.server.fastmcp import FastMCP
from integrations.knowledge_hub.service import KnowledgeHubClient
import logging
from typing import Optional

mcp = FastMCP("Knowledge Hub")
logger = logging.getLogger(__name__)

@mcp.tool()
async def kb_search(query: str, domain: Optional[str] = None) -> str:
    """
    Search the enterprise knowledge base for firm-specific information (HR, IT, Policies, etc.).
    :param query: The search term or question.
    :param domain: Optional category filter (e.g., 'HR', 'IT', 'Finance').
    """
    try:
        client = KnowledgeHubClient()
        results = await client.search(query, domain)
        
        if not results:
            return "No relevant information found in the knowledge base."
        
        output = ["Relevant information from Knowledge Base:"]
        for res in results:
            score = res['metadata'].get('score', 0)
            percentage = round(score * 100, 1)
            output.append(f"Source: {res['metadata']['source']} (Confidence: {percentage}%)")
            output.append(f"Content: {res['content']}")
            output.append("---")
            
        return "\n".join(output)
    except Exception as e:
        logger.error(f"[KnowledgeHubMCP] Search Error: {e}")
        return f"Error searching knowledge base: {str(e)}"

@mcp.tool()
async def kb_list_domains() -> str:
    """List the available knowledge categories (domains) in the enterprise knowledge hub."""
    try:
        client = KnowledgeHubClient()
        domains = await client.list_domains()
        if not domains:
            return "No knowledge domains found."
        return f"Available Knowledge Domains: {', '.join(domains)}"
    except Exception as e:
        logger.error(f"[KnowledgeHubMCP] List Domains Error: {e}")
        return f"Error listing domains: {str(e)}"

@mcp.tool()
async def kb_list_partitions() -> str:
    """List the available organization partitions (folders) in the Knowledge Hub."""
    try:
        client = KnowledgeHubClient()
        partitions = await client.list_partitions()
        if not partitions:
            return "No knowledge partitions found."
        return f"Available Knowledge Partitions: {', '.join(partitions)}"
    except Exception as e:
        logger.error(f"[KnowledgeHubMCP] List Partitions Error: {e}")
        return f"Error listing partitions: {str(e)}"

@mcp.tool()
async def kb_get_source_content(source_name: str) -> str:
    """
    Retrieve the full text of a specific document. Use this when a search snippet is not enough for a complete answer.
    :param source_name: The EXACT name of the source from the search results.
    """
    try:
        client = KnowledgeHubClient()
        data = await client.get_source_content(source_name)
        content = data.get("content", "")
        if not content:
            return f"No content found for document '{source_name}'."
        return f"Full Content for {source_name}:\n\n{content}"
    except Exception as e:
        logger.error(f"[KnowledgeHubMCP] Get Content Error for {source_name}: {e}")
        return f"Error retrieving document content: {str(e)}"

@mcp.tool()
async def kb_update_metadata(source_name: str, domain: Optional[str] = None, partition: Optional[str] = None) -> str:
    """
    Update a document's domain or partition classification. Use this to re-organize knowledge content.
    :param source_name: The filename or source identifier of the document.
    :param domain: New category/domain for the document.
    :param partition: New partition/folder for the document.
    """
    try:
        client = KnowledgeHubClient()
        result = await client.update_metadata(source_name, domain, partition)
        return result
    except Exception as e:
        logger.error(f"[KnowledgeHubMCP] Update Error: {e}")
        return f"Error updating document: {str(e)}"
