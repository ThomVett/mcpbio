# MCP Tool: get_pathway_proteins_from_kegg
# Description: Abstracted tool to resolve a human-readable pathway name to KEGG pathway ID,
# then fetch all human proteins involved, and map to UniProt IDs with metadata using MCP Python SDK.

from mcp.server.fastmcp import FastMCP
import requests
from typing import List, Dict
from urllib.parse import quote
from pydantic import BaseModel
from typing import Any

class PathwayRequest(BaseModel):
    pathway_name: str

class DrugLookupRequest(BaseModel):
    uniprot_ids: List[str]

class DrugInfo(BaseModel):
    chembl_id: str
    name: str
    phase: int

class DrugLookupResponse(BaseModel):
    data: Dict[str, List[DrugInfo]]

# Tool input and output models
from pydantic import BaseModel

class GeneInfo(BaseModel):
    kegg_id: str
    #gene_symbol: str
    uniprot_id: str

class PathwayProteinResponse(BaseModel):
    pathway_name: str
    pathway_id: str
    proteins: List[GeneInfo]

# Step 1: Resolve pathway name to KEGG ID
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

# Step 2: Get KEGG gene IDs from the pathway
def get_pathway_genes(pathway_id: str) -> List[str]:
    # Step 1: Get KO terms linked to the reference pathway map
    map_id = pathway_id.replace("hsa", "map")
    response = requests.get(f"https://rest.kegg.jp/link/ko/{map_id}")
    response.raise_for_status()
    print(f"KO response: {response.text}")
    
    # Handle empty response
    if not response.text.strip():
        print("Warning: No KO terms found for this pathway")
        return []
        
    ko_ids = []
    for line in response.text.strip().split('\n'):
        if line:  # Only process non-empty lines
            parts = line.split('\t')
            if len(parts) >= 2:
                ko_ids.append(parts[1])

    # Step 2: For each KO, get the human gene(s)
    gene_ids = []
    for ko in ko_ids:
        r = requests.get(f"https://rest.kegg.jp/link/hsa/{ko}")
        if r.status_code == 200:
            if r.text.strip():  # Only process if we got a response
                for line in r.text.strip().split('\n'):
                    if line:  # Only process non-empty lines
                        parts = line.split('\t')
                        if len(parts) >= 2:
                            gene_ids.append(parts[1])
    return gene_ids

# Step 3: Convert KEGG gene IDs to UniProt IDs
def convert_genes_to_uniprot(gene_ids: List[str]) -> Dict[str, str]:
    chunk_size = 10
    kegg_to_uniprot = {}
    uniprot_ids = []
    for i in range(0, len(gene_ids), chunk_size):
        chunk = "+".join(gene_ids[i:i+chunk_size])
        response = requests.get(f"https://rest.kegg.jp/conv/uniprot/{chunk}")
        if response.status_code == 200:
            lines = response.text.strip().split('\n')
            for line in lines:
                parts = line.split('\t')
                if len(parts) == 2:
                    kegg_id = parts[0].split(":")[1]
                    uniprot_id = parts[1].split(":")[1]
                    kegg_to_uniprot[kegg_id] = uniprot_id
                    uniprot_ids.append(uniprot_id)
    return kegg_to_uniprot, uniprot_ids

# Step 4: Lookup gene symbols from KEGG gene ID
def get_gene_symbol(kegg_gene_id: str) -> str:
    response = requests.get(f"https://rest.kegg.jp/get/{kegg_gene_id}")
    if response.status_code != 200:
        return "Unknown"
    for line in response.text.strip().split('\n'):
        if line.startswith("NAME"):
            return line.strip()
    return "Unknown"

def get_pathway_proteins(data: PathwayRequest) -> PathwayProteinResponse:
    """
    Retrieves protein information for a given KEGG pathway.
    
    Input:
        data (PathwayRequest): A request object containing:
            - pathway_name (str): Human-readable name of the KEGG pathway (e.g., "N-glycan biosynthesis")
    
    Output:
        Tuple containing:
        1. PathwayProteinResponse object with:
            - pathway_name (str): Original pathway name
            - pathway_id (str): KEGG pathway ID (e.g., "hsa00510")
            - proteins (List[GeneInfo]): List of proteins where each GeneInfo contains:
                - kegg_id (str): KEGG gene identifier
                - gene_symbol (str): Human gene symbol
                - uniprot_id (str): UniProt protein identifier
        2. List[str]: List of UniProt IDs for all proteins in the pathway
    
    Example:
        >>> request = PathwayRequest(pathway_name="N-glycan biosynthesis")
        >>> response, uniprot_ids = get_pathway_proteins(request)
    """
    print(f"▶️ Received pathway_name: {data.pathway_name}")
    pathway_id = get_kegg_pathway_id(data.pathway_name)
    print(f"🔗 Resolved pathway_id: {pathway_id}")
    gene_ids = get_pathway_genes(pathway_id)
    print(f"🧬 Retrieved {len(gene_ids)} gene IDs")
    kegg_to_uniprot, uniprot_ids = convert_genes_to_uniprot(gene_ids)
    print(f"🧪 Mapped {len(kegg_to_uniprot)} genes to UniProt IDs")

    protein_data = []
    print("🔍 Fetching gene symbols and UniProt IDs...")
    for kegg_id in gene_ids:
        #gene_symbol = get_gene_symbol(kegg_id)
        uniprot_id = kegg_to_uniprot.get(kegg_id.replace("hsa:", ""), "Unknown")
        protein_data.append(GeneInfo(kegg_id=kegg_id, uniprot_id=uniprot_id))

    return PathwayProteinResponse(
        pathway_name=data.pathway_name,
        pathway_id=pathway_id,
        proteins=protein_data
    ),uniprot_ids 

def check_uniprot_drug_links(uniprot_ids: List[str]) -> Dict[str, Dict]:
    """
    Checks if proteins (identified by UniProt IDs) are targeted by any drugs in DrugBank.
    
    Input:
        uniprot_ids (List[str]): List of UniProt protein identifiers to check
    
    Output:
        Dict[str, Dict]: Dictionary mapping UniProt IDs to drug information:
            {
                "uniprot_id": {
                    "targeted": bool,  # Whether the protein is targeted by any drugs
                    "drugs": List[str]  # List of drug names targeting this protein
                }
            }
    
    Example:
        >>> uniprot_ids = ["P12345", "Q67890"]
        >>> drug_info = check_uniprot_drug_links(uniprot_ids)
    """
    base_url = "https://rest.uniprot.org/uniprotkb/"
    results = {}

    for uid in uniprot_ids:
        url = f"{base_url}{uid}.json"
        res = requests.get(url)

        if res.status_code != 200:
            results[uid] = {"targeted": False, "drugs": []}
            continue

        data = res.json()
        drug_names = []

        for ref in data.get("uniProtKBCrossReferences", []):
            if ref.get("database") == "DrugBank":
                for prop in ref.get("properties", []):
                    if prop.get("key") == "GenericName":
                        drug_names.append(prop["value"])

        results[uid] = {
            "targeted": bool(drug_names),
            "drugs": drug_names
        }

    return results
# if __name__ == "__main__":


    # # TEST: Change the pathway name here for each test
    # test_pathway = "N-glycan biosynthesis"
    # print("🔬 TESTING FUNCTION: get_pathway_proteins")
    # response, uniprot_ids = get_pathway_proteins(PathwayRequest(pathway_name=test_pathway))
    # print("✅ Response:", response)
    # print("✅ UniProt IDs:", uniprot_ids)
   
    # print(check_uniprot_drug_links(uniprot_ids ))
