from typing import List, Any
from pydantic import BaseModel, Field


class APIAccessMethod(BaseModel):
    function_name: str = Field(description="The name of the function to call")
    description: str = Field(
        description="A detailed description of what this method does"
    )
    return_value: str = Field(
        description="Description of what is returned by this method"
    )
    example: str = Field(description="Example input in JSON format")


class Tool(BaseModel):
    name: str = Field(description="The name of the tool")
    description: str = Field(
        description="A comprehensive description of the tool's purpose and capabilities"
    )
    use_cases: List[str] = Field(
        description="List of specific use cases where this tool is useful"
    )
    api_access_methods: List[APIAccessMethod] = Field(
        description="Methods available to access this tool's API"
    )

    depends_on: str = Field(
        default=None,
        description="If the tool depends on another tool - specify the tool name here."
    )

    output: Any = Field(
        default=None,
        description="attribute to store the outputs of the previous step"
    )

    def tool_call(self):
        pass


class KEGGTool(Tool):
    def tool_call(self):
        pass


kegg = KEGGTool(
    name="KEGG",
    description="KEGG provides access to pathway and network information related to genes, proteins, and metabolites.",
    use_cases=[
        "Discover which pathways a gene is involved in",
        "Retrieve all proteins in a known pathway",
        "Analyze how mutations may impact cellular signaling",
    ],
    api_access_methods=[
        APIAccessMethod(
            function_name="get_pathway_proteins",
            description="Use when you have a pathway name and want to list all proteins in that pathway.",
            return_value="list of genes/proteins with IDs and names",
            example='{ "pathway_name": "apoptosis" }',
        )
    ],
)

go_terms = Tool(
    name="GO",
    description="GO is the gene ontology database and provides general information about genes",
    use_cases=["Find genes with functional similarity to one another"],
    api_access_methods=[
        APIAccessMethod(
            function_name="get_similar_genes",
            description="find all the genes that are similar to the inut genes",
            return_value="List of similar genes",
            example='{"gene_name": "TP53"}',
        )
    ],
)


class DrugBankTool(Tool):
    def tool_call(self, inputs: None):
        return input


drug_bank = DrugBankTool(
    name="DrugBank",
    description="DrugBank provides information on drug molecules, including approved and investigational compounds, their targets, mechanisms of action, and clinical indications.",
    use_cases=[
        "Identify drugs that target a specific gene or protein",
        "Check if a gene is a known drug target",
        "Look up drugs in development or approved for a disease",
    ],
    api_access_methods=[
        APIAccessMethod(
            function_name="search_drug",
            description="Search for drugs by name, target, or indication",
            return_value="Drug information including targets and indications",
            example='{ "target": "TP53" }',
        )
    ],
)


# class UniProt(Tool):
#     name = "UniProt"
#     description = "UniProt provides detailed protein-level information including: Protein sequence and function, Domains and sites (e.g., active site, binding site), Gene and protein names, Post-translational modifications, Protein variants (natural or disease-associated)"
#     use_cases = ["Finding the function of a gene or protein (e.g., TP53)", "Locating domains affected by mutations", "Checking involvement in biological processes or pathways"]
#     api_access_methods = [
#         APIAccessMethod(
#             function_name="search_uniprot",
#             description="Search UniProt for information about a protein",
#             return_value="JSON with protein details",
#             example='{ "query": "gene:TP53 AND organism_id:9606", "format": "json" }'
#         )
#     ]


# class ClinVar(Tool):
#     name = "ClinVar"
#     description = "ClinVar provides information about genetic variation and its relationship to human health."
#     use_cases = ["Finding the clinical significance of a genetic variant", "Locating variants associated with a specific condition", "Checking the frequency of a variant in a population"]
#     api_access_methods = [
#         APIAccessMethod(
#             function_name="search_variant",
#             description="Search for information about a genetic variant",
#             return_value="Summary of clinical significance and related conditions",
#             example='{ "variant_id": "rs12345" }'
#         )
#     ]


# class ChEMBL(Tool):
#     name = "ChEMBL"
#     description = "ChEMBL is a database of bioactive drug-like molecules that includes information on their bioactivities, targets, and properties."
#     use_cases = ["Identify compounds with potent activity against a protein", "Explore drug candidates not yet approved", "Analyze IC50/Ki data for known ligands"]
#     api_access_methods = [
#         APIAccessMethod(
#             function_name="search_target",
#             description="Search for a target in ChEMBL",
#             return_value="Target information and related bioactivities",
#             example='{ "query": "TP53" }'
#         )
#     ]


# class STRING(Tool):
#     name = "STRING"
#     description = "STRING is a protein–protein interaction database that integrates known and predicted associations from multiple sources."
#     use_cases = ["Identify interaction partners of a gene/protein", "Explore functional protein networks", "Infer indirect effects of gene mutations"]
#     api_access_methods = [
#         APIAccessMethod(
#             function_name="get_interactions",
#             description="Get interaction partners for a protein",
#             return_value="Network of protein interactions with confidence scores",
#             example='{ "identifiers": "TP53", "species": 9606 }'
#         )
#     ]


# Individual tool prompts
kegg_prompt = """
API TOOL: KEGG

DESCRIPTION:
KEGG provides access to pathway and network information related to genes, proteins, and metabolites.

RELEVANT USE CASES:
- Discover which pathways a gene is involved in
- Retrieve all proteins in a known pathway
- Analyze how mutations may impact cellular signaling

API ACCESS METHODS:
1. `get_pathway_proteins(pathway_name: str)`
   - Use when you have a pathway name and want to list all proteins in that pathway.
   - Returns: list of genes/proteins with IDs and names
   - Example: `{ "pathway_name": "apoptosis" }`

NOTE:
- Always use organism code `"hsa"` for human.
- Chain these calls when needed: first retrieve the `pathway_id`, then get the proteins.
"""

uniprot_prompt = """
API TOOL: UniProt
DESCRIPTION:
UniProt provides detailed protein-level information including:
- Protein sequence and function
- Domains and sites (e.g., active site, binding site)
- Gene and protein names
- Post-translational modifications
- Protein variants (natural or disease-associated)

RELEVANT USE CASES:
- Finding the function of a gene or protein (e.g., TP53)
- Locating domains affected by mutations
- Checking involvement in biological processes or pathways

API ACCESS:
Base URL: https://rest.uniprot.org/uniprotkb/search
Example query: https://rest.uniprot.org/uniprotkb/search?query=gene:TP53+AND+organism_id:9606&format=json

Useful fields:
- `proteinDescription.recommendedName.fullName.value`
- `comments`, `features`
"""

clinvar_prompt = """
API TOOL: ClinVar
DESCRIPTION:
ClinVar reports the clinical significance of gene variants, such as whether a mutation is pathogenic, benign, or uncertain.

RELEVANT USE CASES:
- Determine if a mutation (e.g., KRAS G12D) is clinically significant
- Retrieve disease associations and review status

API ACCESS:
Base URL: https://api.ncbi.nlm.nih.gov/variation/v0/

Example query (by HGVS or rsID): https://api.ncbi.nlm.nih.gov/variation/v0/refsnp/12345  
Entrez search by gene/mutation: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=clinvar&term=KRAS%20G12D

Useful fields:
- `clinical_significance.description`
- `rcv.conditions.name`
- `review_status`
- `gene.name`
"""

drugbank_prompt = """
API TOOL: DrugBank

DESCRIPTION:
DrugBank provides information on drug molecules, including approved and investigational compounds, their targets, mechanisms of action, and clinical indications.

RELEVANT USE CASES:
- Identify drugs that target a specific gene or protein
- Check if a gene is a known drug target
- Look up drugs in development or approved for a disease

ACCESS:
- API available to licensed users (academic/commercial)
- Public queries possible via DrugBank XML or search forms

Example queries:
- Find drugs targeting TP53
- Look up all drugs for "non-small cell lung cancer"
- Retrieve drug info by ID (e.g., DB01234)

USEFUL FIELDS:
- `name`, `targets`, `indication`
- `mechanism-of-action`, `clinical-trials`, `categories`

NOTES:
- Drugs and genes are linked by target annotations
- DrugBank IDs begin with "DB" (e.g., DB01053)
- Overlap with ChEMBL and UniProt for drug-target mappings
"""

chembel_prompt = """
API TOOL: ChEMBL

DESCRIPTION:
ChEMBL is a database of bioactive drug-like molecules that includes information on their bioactivities, targets, and properties. It is widely used for drug discovery and target validation.

RELEVANT USE CASES:
- Identify compounds with potent activity against a protein
- Explore drug candidates not yet approved
- Look up chemical structures and mechanisms
- Analyze IC50/Ki data for known ligands

API ACCESS:
Base URL: https://www.ebi.ac.uk/chembl/api/data/

Example endpoints:
- Search target: /target/search.json?q=TP53
- Get target ID: CHEMBL3927
- Search for bioactivities: /activity.json?target_chembl_id=CHEMBL3927
- Retrieve compound info: /molecule/CHEMBL25

USEFUL FIELDS:
- `activity_type` and `standard_value` (e.g., IC50: 42 nM)
- `molecule_chembl_id`
- `target_chembl_id`
- `canonical_smiles` for chemical structure

NOTES:
- Gene → Target → Bioactivity pipeline
- Molecules here may not be approved but may be highly active
- ChEMBL is ideal for drug repurposing or novel candidate search
"""

string_prompt = """
API TOOL: STRING

DESCRIPTION:
STRING is a protein–protein interaction database that integrates known and predicted associations from multiple sources including experiments, computational prediction, and literature mining.

RELEVANT USE CASES:
- Identify interaction partners of a gene/protein
- Explore functional protein networks
- Infer indirect effects of gene mutations
- Suggest alternative or adjacent drug targets

API ACCESS:
Base URL: https://string-db.org/api/

Example endpoints:
- Get interaction partners: /json/network?identifiers=TP53&species=9606
- Filtered interactions: /json/interaction_partners?identifiers=TP53&species=9606
- Pathway enrichment: /json/enrichment?identifiers=TP53&species=9606

NOTES:
- `species=9606` = Homo sapiens
- Scores range 0–1000 (higher = more confidence)
- Can query by gene/protein names or STRING IDs
- Integrate with UniProt and KEGG for deeper biological context
"""
