from typing import Any, List, Tuple
import httpx
from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
import kegg
import go

# Initialize FastMCP server
mcp = FastMCP("weather")

# Initialize FastAPI app
app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Constants

KEGG_API_BASE = "https://rest.kegg.jp"





@mcp.tool()
async def kegg_pathway_proteins(pathway_name: str) -> str:
    """Get proteins in a biological pathway from KEGG.
    
    Args:
        pathway_name: Name of the pathway (e.g., apoptosis)

    """

    organism = "hsa"

    # First get the pathway ID
    pathway_id, pathway_desc = await kegg.get_pathway_id(pathway_name, organism)
    
    if not pathway_id:
        return f"No pathway found matching '{pathway_name}' for organism {organism}"
    
    # Get the proteins for this pathway
    proteins = await kegg.get_pathway_proteins(pathway_id, organism)
    
    if not proteins:
        return f"No genes found in pathway {pathway_desc} ({pathway_id})"
    
    # Format the result
    result = f"Pathway: {pathway_desc} ({pathway_id})\n"
    result += f"Number of genes/proteins: {len(proteins)}\n\n"
    result += "Proteins:\n"
    
    protein_lines = []
    for protein in proteins:
        if "name" in protein:
            protein_lines.append(f"{protein['id']}: {protein['name']}")
        else:
            protein_lines.append(protein['id'])
            
    result += "\n".join(protein_lines)
    
    return result


@mcp.tool()
async def go_functional_similarity(gene_name: str) -> List[str]:
    """Gets a list of genes that are similar to gene name according to their gene ontology

    Args:
        gene_name: Gene name to query the functional similarity

    Returns:
        List of genes
    """

    return go.find_similar_genes(gene_name)



@mcp.tool()
async def get_proteins_that_are_in_too_lists(protein_list_1: List[str], protein_list_2: List[str]) -> List[str]:
    """Based on the two input protein lists returns the proteis that are present in the two protein lists"""

    # Convert both lists to sets for faster lookup and remove duplicates
    set1 = {protein.strip().lower() for protein in protein_list_1}
    set2 = {protein.strip().lower() for protein in protein_list_2}
    
    # Find the intersection of the two sets to get proteins present in both lists
    common_proteins = set1.intersection(set2)
    
    # Convert the set back to a list and return it
    return list(common_proteins)

if __name__ == "__main__":
    mcp.run(transport='stdio')