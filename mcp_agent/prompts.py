kegg_prompt = """
API TOOL: KEGG

DESCRIPTION:
KEGG provides access to pathway and network information related to genes, proteins, and metabolites.

RELEVANT USE CASES:
- Discover which pathways a gene is involved in
- Retrieve all proteins in a known pathway
- Analyze how mutations may impact cellular signaling

API ACCESS METHODS:
1. `get_pathway_id(pathway_name: str, organism: str = "hsa")`
   - Use when you have the **name** of a biological pathway (e.g., "apoptosis") and want to retrieve its KEGG ID (e.g., `hsa04210`).
   - Returns a tuple: `(pathway_id, pathway_description)`
   - Example: `{ "pathway_name": "apoptosis" }`

2. `get_pathway_proteins(pathway_id: str, organism: str = "hsa")`
   - Use when you have a KEGG **pathway ID** and want to list all proteins in that pathway.
   - Returns: list of genes/proteins with IDs and names
   - Example: `{ "pathway_id": "hsa04210" }`

NOTE:
- Always use organism code `"hsa"` for human.
- Chain these calls when needed: first retrieve the `pathway_id`, then get the proteins.
"""