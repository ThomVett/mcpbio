from typing import List, Tuple, Optional, Dict, Any
import httpx

# Constants
KEGG_API_BASE = "https://rest.kegg.jp"

async def get_pathway_id(pathway_name: str, organism: str = "hsa") -> Tuple[Optional[str], Optional[str]]:
    """Get KEGG pathway ID from a pathway name.
    
    Args:
        pathway_name: Name of the pathway (e.g., apoptosis)
        organism: KEGG organism code (default: hsa for human)
        
    Returns:
        Tuple of (pathway_id, pathway_description) or (None, None) if not found
    """
    # Get the list of all pathways for this organism
    list_url = f"{KEGG_API_BASE}/list/pathway/{organism}"
    
    async with httpx.AsyncClient() as client:
        try:
            # Get all pathways
            response = await client.get(list_url, timeout=30.0)
            response.raise_for_status()
            
            # Parse response to find pathway ID matching the name
            pathway_name_lower = pathway_name.lower()
            
            for line in response.text.strip().split('\n'):
                if line and pathway_name_lower in line.lower():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        pathway_id = parts[0].strip()
                        pathway_desc = parts[1].strip()
                        return pathway_id, pathway_desc
            
            return None, None
                
        except Exception as e:
            print(f"Error fetching pathway ID: {str(e)}")
            return None, None

async def get_pathway_proteins(pathway_id: str, organism: str = "hsa") -> List[Dict[str, str]]:
    """Get proteins in a biological pathway from KEGG.
    
    Args:
        pathway_id: KEGG pathway ID (e.g., hsa04210 for apoptosis)
        organism: KEGG organism code (default: hsa for human)
        
    Returns:
        List of dictionaries with gene information (id, name)
    """
    async with httpx.AsyncClient() as client:
        try:
            # Get genes/proteins in this pathway
            link_url = f"{KEGG_API_BASE}/link/{organism}/{pathway_id}"
            response = await client.get(link_url, timeout=30.0)
            response.raise_for_status()
            
            # Parse genes
            genes = []
            for line in response.text.strip().split('\n'):
                if line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        gene_id = parts[1].strip()
                        genes.append(gene_id)
            
            if not genes:
                return []
            
            # Get gene information
            result = []
            for i in range(0, len(genes), 10):  # Process in batches of 10
                batch = genes[i:i+10]
                genes_str = "+".join(batch)
                info_url = f"{KEGG_API_BASE}/get/{genes_str}"
                response = await client.get(info_url, timeout=30.0)
                
                # Parse gene info
                current_gene = None
                gene_info = {}
                
                for line in response.text.split('\n'):
                    if line.startswith("ENTRY"):
                        if current_gene and gene_info:
                            result.append(gene_info)
                        current_gene = line.split()[1]
                        gene_info = {"id": current_gene}
                    elif line.startswith("NAME") and current_gene:
                        gene_info["name"] = line.replace("NAME", "").strip()
                
                # Add the last gene
                if current_gene and gene_info:
                    result.append(gene_info)
            
            return result
                
        except Exception as e:
            print(f"Error fetching pathway proteins: {str(e)}")
            return [] 