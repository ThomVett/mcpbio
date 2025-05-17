import requests
import json
import sys

def get_gene_id(gene_symbol):
    """Get HGNC ID for a given gene symbol"""
    url = f"http://mygene.info/v3/query?q={gene_symbol}&species=human&fields=HGNC"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error fetching gene ID: {response.status_code}")
        return None
    
    data = response.json()
    if data['hits'] and 'HGNC' in data['hits'][0]:
        hgnc_id = data['hits'][0]['HGNC']
        return f"HGNC:{hgnc_id}"
    else:
        print(f"Could not find HGNC ID for {gene_symbol}")
        return None

def get_gene_go_terms(gene_id):
    """Retrieve GO terms associated with a gene"""
    url = f"http://api.geneontology.org/api/bioentity/gene/{gene_id}/function"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error fetching GO terms: {response.status_code}")
        return []
    go_data = response.json()
    # Extract GO term IDs
    go_terms = [association['object']['id'] for association in go_data['associations'] 
                if 'object' in association and 'id' in association['object']]
    return go_terms

def get_genes_for_go_term(go_term_id, limit=100):
    """Get genes associated with a specific GO term"""
    url = f"http://api.geneontology.org/api/bioentity/function/{go_term_id}/genes"
    params = {
        "rows": limit,
        "facet": "false"
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"Error fetching genes for {go_term_id}: {response.status_code}")
        return []
    
    try:
        gene_data = response.json()
        # Extract gene symbols
        genes = []
        if 'associations' in gene_data:
            for association in gene_data['associations']:
                if 'subject' in association and 'label' in association['subject']:
                    genes.append(association['subject']['label'])
        return genes
    except json.JSONDecodeError:
        print(f"Error parsing JSON for {go_term_id}")
        return []

def find_similar_genes(gene_symbol, max_go_terms=3):
    """Find functionally similar genes to the input gene"""
    print(f"Finding genes functionally similar to {gene_symbol}...")
    
    # Get gene ID
    gene_id = get_gene_id(gene_symbol)
    if not gene_id:
        return []
    
    # Get GO terms
    print(f"Fetching GO terms for {gene_symbol}...")
    go_terms = get_gene_go_terms(gene_id)
    print(f"Found {len(go_terms)} GO terms associated with {gene_symbol}")
    
    # Get genes for each GO term
    all_genes = set()  # Use a set to avoid duplicates
    for go_term in go_terms[:max_go_terms]:  # Limit to avoid too many requests
        print(f"Fetching genes for GO term: {go_term}")
        genes_for_term = get_genes_for_go_term(go_term)
        all_genes.update(genes_for_term)
    
    # Remove the input gene from results
    genes_list = sorted(list(all_genes))
    if gene_symbol in genes_list:
        genes_list.remove(gene_symbol)
    
    return genes_list

def main():
    # Get gene from command line or use default
    if len(sys.argv) > 1:
        gene = sys.argv[1]
    else:
        gene = "TP53"
    
    # Find similar genes
    similar_genes = find_similar_genes(gene)
    
    # Output results
    print(f"\nFound {len(similar_genes)} genes functionally similar to {gene}:")
    for gene in similar_genes:
        print(gene)
    
    print(f"\nTotal: {len(similar_genes)} genes functionally similar to {gene}")

if __name__ == "__main__":
    main()