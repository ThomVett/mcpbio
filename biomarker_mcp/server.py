from mcp.server.fastmcp import FastMCP
from mcp_kegg_protein_tool import get_pathway_proteins, PathwayRequest, PathwayProteinResponse

mcp = FastMCP("KEGG Protein Tool")

@mcp.tool(name="get_pathway_proteins_from_kegg")
def wrapper(data: PathwayRequest) -> PathwayProteinResponse:
    return get_pathway_proteins(data)

if __name__ == "__main__":
    mcp.run()
