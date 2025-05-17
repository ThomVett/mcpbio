# server.py
from mcp.server.fastmcp import FastMCP
import requests
from urllib.parse import quote

# Create an MCP server
mcp = FastMCP("Demo")


@mcp.tool()
def get_kegg_pathway_id(pathway_name: str) -> str:
    encoded_name = quote(str(pathway_name))
    
    print(f"🔎 KEGG query: https://rest.kegg.jp/find/pathway/{encoded_name}")
    response = requests.get(f"https://rest.kegg.jp/find/pathway/{encoded_name}")
    response.raise_for_status()
    lines = response.text.strip().split('\n')
    for line in lines:
        if "path:map" in line:
            # Extract the pathway ID (e.g., "00510" from "path:map00510")
            pathway_id = line.split('\t')[0].split("path:map")[1]
            return f"hsa{pathway_id}"  # Convert to human pathway format
    raise ValueError("Human KEGG pathway not found")


# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"