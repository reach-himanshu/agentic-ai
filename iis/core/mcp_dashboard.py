from fastapi.responses import HTMLResponse
from mcp.server.fastmcp import FastMCP
import inspect
import mcp.types as types

async def render_mcp_dashboard(mcp_server) -> HTMLResponse:
    """
    Renders a premium-looking dashboard for an MCP server, showing Tools, Prompts, and Resources.
    """
    # Detect server type and name
    if hasattr(mcp_server, "name"):
        server_name = mcp_server.name
    else:
        server_name = "MCP Server"

    # Extract Tools
    tools = []
    try:
        raw_tools = []
        # FastMCP support
        if hasattr(mcp_server, "list_tools") and not hasattr(mcp_server, "server"):
            raw_tools = await mcp_server.list_tools()
        # FastApiMCP or direct server support
        elif hasattr(mcp_server, "tools"):
            raw_tools = mcp_server.tools
        
        # If it's a ListToolsResult object, extract the list
        if hasattr(raw_tools, "tools"):
            raw_tools = raw_tools.tools

        if isinstance(raw_tools, list):
            for tool in raw_tools:
                params = []
                # Try to get parameters from function signature (FastMCP)
                func = getattr(tool, "func", None)
                if func:
                    try:
                        sig = inspect.signature(func)
                        for name, param in sig.parameters.items():
                            params.append({
                                "name": name,
                                "type": str(param.annotation).replace("typing.", ""),
                                "default": str(param.default) if param.default != inspect.Parameter.empty else "Required"
                            })
                    except Exception:
                        pass
                # Fallback to inputSchema (FastApiMCP / Pydantic)
                elif hasattr(tool, "inputSchema") and isinstance(tool.inputSchema, dict):
                    props = tool.inputSchema.get("properties", {})
                    required = tool.inputSchema.get("required", [])
                    for name, prop in props.items():
                        params.append({
                            "name": name,
                            "type": prop.get("type", "any"),
                            "default": "Required" if name in required else "Optional"
                        })

                tools.append({
                    "name": getattr(tool, "name", "Unknown"),
                    "description": getattr(tool, "description", "No description provided."),
                    "parameters": params
                })
    except Exception as e:
        logger.error(f"Error extracting tools: {e}")

    # Extract Prompts
    prompts = []
    try:
        raw_prompts = []
        if hasattr(mcp_server, "list_prompts") and not hasattr(mcp_server, "server"):
            raw_prompts = await mcp_server.list_prompts()
        elif hasattr(mcp_server, "_prompts"):
            raw_prompts = mcp_server._prompts
            
        if hasattr(raw_prompts, "prompts"):
            raw_prompts = raw_prompts.prompts

        if isinstance(raw_prompts, list):
            for prompt in raw_prompts:
                prompts.append({
                    "name": getattr(prompt, "name", "Unknown"),
                    "description": getattr(prompt, "description", "No description provided.")
                })
    except Exception as e:
        logger.error(f"Error extracting prompts: {e}")

    # Extract Resources
    resources = []
    try:
        raw_resources = []
        if hasattr(mcp_server, "list_resources") and not hasattr(mcp_server, "server"):
            raw_resources = await mcp_server.list_resources()
        elif hasattr(mcp_server, "_resources"):
            raw_resources = mcp_server._resources

        if hasattr(raw_resources, "resources"):
            raw_resources = raw_resources.resources

        if isinstance(raw_resources, list):
            for resource in raw_resources:
                resources.append({
                    "name": getattr(resource, "name", "Unknown"),
                    "uri": str(getattr(resource, "uri", "Unknown")),
                    "description": getattr(resource, "description", "No description provided.")
                })
    except Exception as e:
        logger.error(f"Error extracting resources: {e}")

    try:
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{server_name} - MCP Documentation</title>
            <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600&family=Inter:wght@400;500&display=swap" rel="stylesheet">
            <style>
                :root {{
                    --primary: #6366f1;
                    --bg: #0f172a;
                    --card: #1e293b;
                    --text: #f8fafc;
                    --text-muted: #94a3b8;
                    --accent: #818cf8;
                    --success: #10b981;
                    --warning: #f59e0b;
                    --info: #3b82f6;
                }}
                body {{
                    font-family: 'Inter', sans-serif;
                    background-color: var(--bg);
                    color: var(--text);
                    margin: 0;
                    padding: 40px 20px;
                    line-height: 1.6;
                }}
                .container {{
                    max-width: 1000px;
                    margin: 0 auto;
                }}
                header {{
                    margin-bottom: 40px;
                    text-align: center;
                }}
                h1 {{
                    font-family: 'Outfit', sans-serif;
                    font-size: 3rem;
                    margin: 0;
                    background: linear-gradient(135deg, #fff 0%, var(--accent) 100%);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                }}
                .description {{
                    color: var(--text-muted);
                    font-size: 1.1rem;
                    margin-top: 10px;
                }}
                section {{
                    margin-bottom: 60px;
                }}
                h2 {{
                    font-family: 'Outfit', sans-serif;
                    font-size: 1.8rem;
                    border-bottom: 2px solid rgba(255,255,255,0.05);
                    padding-bottom: 10px;
                    margin-bottom: 24px;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                }}
                .card-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(450px, 1fr));
                    gap: 20px;
                }}
                .mcp-card {{
                    background: var(--card);
                    border-radius: 16px;
                    padding: 24px;
                    border: 1px solid rgba(255,255,255,0.05);
                    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
                    transition: transform 0.2s, box-shadow 0.2s;
                }}
                .mcp-card:hover {{
                    transform: translateY(-4px);
                    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
                    border-color: rgba(99, 102, 241, 0.3);
                }}
                .card-header {{
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    margin-bottom: 12px;
                }}
                .card-title {{
                    font-family: 'Outfit', sans-serif;
                    font-size: 1.3rem;
                    font-weight: 600;
                    color: var(--accent);
                }}
                .badge {{
                    padding: 2px 10px;
                    border-radius: 99px;
                    font-size: 0.75rem;
                    font-weight: 500;
                    text-transform: uppercase;
                }}
                .badge-tool {{ background: rgba(16, 185, 129, 0.1); color: var(--success); border: 1px solid rgba(16, 185, 129, 0.2); }}
                .badge-prompt {{ background: rgba(245, 158, 11, 0.1); color: var(--warning); border: 1px solid rgba(245, 158, 11, 0.2); }}
                .badge-resource {{ background: rgba(59, 130, 246, 0.1); color: var(--info); border: 1px solid rgba(59, 130, 246, 0.2); }}
                
                .card-desc {{
                    margin-bottom: 16px;
                    color: var(--text-muted);
                    font-size: 0.95rem;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 10px;
                    font-size: 0.85rem;
                }}
                th {{
                    text-align: left;
                    padding: 8px;
                    border-bottom: 1px solid rgba(255,255,255,0.1);
                    color: var(--text-muted);
                    font-weight: 500;
                }}
                td {{
                    padding: 10px 8px;
                    border-bottom: 1px solid rgba(255,255,255,0.05);
                }}
                code {{
                    background: rgba(0,0,0,0.3);
                    padding: 2px 6px;
                    border-radius: 4px;
                    font-family: monospace;
                    color: #fca5a5;
                }}
                .transport-info {{
                    margin-top: 60px;
                    padding: 30px;
                    background: rgba(99, 102, 241, 0.05);
                    border-radius: 16px;
                    border: 1px dashed rgba(99, 102, 241, 0.3);
                    text-align: center;
                }}
                .uri-text {{
                    color: #93c5fd;
                    font-family: monospace;
                    word-break: break-all;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>{server_name}</h1>
                    <p class="description">Model Context Protocol (MCP) Dashboard</p>
                </header>

                <!-- TOOLS SECTION -->
                <section id="tools">
                    <h2>Tools <span class="badge badge-tool">{len(tools)}</span></h2>
                    <div class="card-grid">
                        {"".join([f'''
                        <div class="mcp-card">
                            <div class="card-header">
                                <div class="card-title">{tool["name"]}</div>
                                <div class="badge badge-tool">Tool</div>
                            </div>
                            <div class="card-desc">{tool["description"]}</div>
                            <table>
                                <thead>
                                    <tr>
                                        <th>Parameter</th>
                                        <th>Type</th>
                                        <th>Default</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {"".join([f"""
                                    <tr>
                                        <td><code>{p["name"]}</code></td>
                                        <td>{p["type"]}</td>
                                        <td>{p["default"]}</td>
                                    </tr>
                                    """ for p in tool["parameters"]])}
                                </tbody>
                            </table>
                        </div>
                        ''' for tool in tools])}
                    </div>
                </section>

                <!-- PROMPTS SECTION -->
                {"".join([f'''
                <section id="prompts">
                    <h2>Prompts <span class="badge badge-prompt">{len(prompts)}</span></h2>
                    <div class="card-grid">
                        {"".join([f"""
                        <div class="mcp-card">
                            <div class="card-header">
                                <div class="card-title">{prompt["name"]}</div>
                                <div class="badge badge-prompt">Prompt</div>
                            </div>
                            <div class="card-desc">{prompt["description"]}</div>
                        </div>
                        """ for prompt in prompts])}
                    </div>
                </section>
                ''' if prompts else ""])}

                <!-- RESOURCES SECTION -->
                {"".join([f'''
                <section id="resources">
                    <h2>Resources <span class="badge badge-resource">{len(resources)}</span></h2>
                    <div class="card-grid">
                        {"".join([f"""
                        <div class="mcp-card">
                            <div class="card-header">
                                <div class="card-title">{resource["name"]}</div>
                                <div class="badge badge-resource">Resource</div>
                            </div>
                            <div class="card-desc">{resource["description"]}</div>
                            <div class="uri-text">URI: {resource["uri"]}</div>
                        </div>
                        """ for resource in resources])}
                    </div>
                </section>
                ''' if resources else ""])}

                <div class="transport-info">
                    <strong>MCP SSE Server:</strong> Operational<br>
                    <small style="color: var(--text-muted)">Exposing Prompts, Tools, and Resources via Model Context Protocol</small>
                </div>
            </div>
        </body>
        </html>
        """
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"HTML generation error: {e}")
        return HTMLResponse(content="<html><body><h1>Dashboard Error</h1><p>An unexpected error occurred. Please contact support.</p></body></html>", status_code=500)
