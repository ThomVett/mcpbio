import sys
import traceback
from mcp.server.fastmcp import FastMCP

# Add debug output immediately
print("Starting server script...", file=sys.stderr)

try:
    # Import the necessary functions and classes from your module
    print("Attempting to import from mcp_kegg_protein_tool...", file=sys.stderr)
    from mcp_kegg_protein_tool import (
        get_pathway_proteins,
        check_uniprot_drug_links,
        PathwayRequest,
        PathwayProteinResponse,
        DrugLookupRequest,
        DrugInfo,
        DrugLookupResponse
    )
    print("Imports successful!", file=sys.stderr)
except ImportError as e:
    print(f"Import error: {str(e)}", file=sys.stderr)
    print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
    raise

# Initialize the MCP server
print("Creating FastMCP instance...", file=sys.stderr)
try:
    mcp = FastMCP("KEGG Protein Tool")
    print("FastMCP instance created successfully", file=sys.stderr)
except Exception as e:
    print(f"Error creating FastMCP instance: {str(e)}", file=sys.stderr)
    print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
    raise

# Tool 1: Get pathway proteins
print("Registering get_pathway_proteins_from_kegg tool...", file=sys.stderr)
@mcp.tool(name="get_pathway_proteins_from_kegg", description="Retrieves protein information from KEGG pathways.", annotations={"mcp_server": "KEEG"})
def get_proteins_tool(data: PathwayRequest) -> PathwayProteinResponse:
    """Retrieves protein information from KEGG pathways.
    
    This tool takes a KEGG pathway name and returns a list of proteins associated with that pathway.
    The response includes UniProt IDs and other relevant protein information that can be used for
    further analysis or drug interaction lookups.
    
    Args:
        data (PathwayRequest): A request containing the KEGG pathway name to query
        
    Returns:
        PathwayProteinResponse: A response containing the list of proteins found in the pathway
    """
    print(f"Tool called with pathway: {data.pathway_name}", file=sys.stderr)
    response, _ = get_pathway_proteins(data)
    return response

# Tool 2: Lookup drugs for UniProt IDs
print("Registering check_drug_links_for_uniprot_ids tool...", file=sys.stderr)
@mcp.tool(name="check_drug_links_for_uniprot_ids", description="Looks up drug interactions for given UniProt protein IDs.", annotations={"mcp_server": "KEEG"})
def drug_lookup_tool(data: DrugLookupRequest) -> DrugLookupResponse:
    """Looks up drug interactions for given UniProt protein IDs.
    
    This tool takes a list of UniProt IDs and checks for any known drug interactions or
    associations with these proteins. It returns information about drugs that interact
    with the specified proteins, including drug names and development phases.
    
    Args:
        data (DrugLookupRequest): A request containing a list of UniProt IDs to check
        
    Returns:
        DrugLookupResponse: A response containing drug interaction information for each UniProt ID
    """
    print(f"Tool called with UniProt IDs: {data.uniprot_ids}", file=sys.stderr)
    raw_result = check_uniprot_drug_links(data.uniprot_ids)
    result = {}

    for uid, info in raw_result.items():
        drugs = [DrugInfo(chembl_id="", name=d, phase=0) for d in info["drugs"]]
        result[uid] = drugs

    return DrugLookupResponse(data=result)

print("Tools registered successfully", file=sys.stderr)

if __name__ == "__main__":
    print("Starting MCP server...", file=sys.stderr)
    try:
        # Start the MCP server
        mcp.run()
    except Exception as e:
        print(f"Error running MCP server: {str(e)}", file=sys.stderr)
        print(f"Traceback: {traceback.format_exc()}", file=sys.stderr)
        sys.exit(1)