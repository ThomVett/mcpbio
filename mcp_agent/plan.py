import asyncio

from openai import OpenAI
import json

import kegg
from keys import together_ai_api_key
from prompts import kegg_prompt

client = OpenAI(api_key=together_ai_api_key,  base_url="https://api.together.xyz/v1")



planing_prompt = f"""
You are a biomedical API planner.

You are given access to a set of bioinformatics APIs. Your job is to:
- Understand the user's question
- Decide which APIs are needed to answer it
- Output a structured JSON plan detailing which API to use, in which order, and what parameters

Respond ONLY in JSON format like this:
{{
  "task": "short_task_label",
  "steps": [
    {{
      "action": "api_name",
      "description": "What this step does (in plain English).",
      "params": {{
        "function": "api_function_name_if_applicable",
        "key": "value"
      }}
    }}
  ]
}}


Below are descriptions of available APIs:

---

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

---

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

---

{kegg_prompt}
---

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

---

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

---

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

STEPS_ENRICHMENT = {
    "clinvar": "This helps understand the medical relevance of the variant.",
    "drugbank": "This could highlight therapeutic opportunities.",
    "uniprot": "This reveals key information about the protein’s role and function.",
    "string": "This helps identify interacting proteins and broader functional networks.",
    "chembl": "This may uncover experimental compounds or drugs under development.",
    "kegg": "This provides insight into the biological pathways the gene participates in."
}

def explain_personalized_steps(plan_json):

    steps = plan_json.get("steps", [])
    if not steps:
        return "No steps were found in the planning output."

    readable_steps = []

    for i, step in enumerate(steps, 1):
        db = step.get("action", "").strip().lower()
        db_name = db.capitalize()

        # Ensure both description and enrichment end with a period
        description = step.get("description", "").strip()
        if not description.endswith('.'):
            description += '.'

        extra = STEPS_ENRICHMENT.get(db, "")
        if extra and not extra.endswith('.'):
            extra += '.'

        final_text = f"**Step {i} – Querying {db_name}**\n{description} {extra}".strip()
        readable_steps.append(final_text)

    return "\n\n".join(readable_steps)




def generate_bio_plan(user_query: str):

    user_prompt = f"User query: \"{user_query}\""

    print(planing_prompt)
    response = client.chat.completions.create(model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",  # Or llama-2-70b-chat, nous-hermes, etc.
    messages=[
        {"role": "system", "content": planing_prompt},
        {"role": "user", "content": user_prompt}
    ],
    temperature=0.2,
    max_tokens=1000)


    output = response.choices[0].message.content

    try:
        json_start = output.find("{")
        return json.loads(output[json_start:])
    except Exception as e:
        print("Failed to parse JSON response:", e)
        print("LLM raw output:", output)
        return None


async def execute_bio_plan(plan):
    results = []

    for step in plan.get("steps", []):
        action = step.get("action", "").lower()
        params = step.get("params", {})
        function = params.get("function", "").lower()

        if action == "kegg":
            if function == "get_pathway_id":
                pathway_name = params.get("pathway_name")
                organism = params.get("organism", "hsa")
                if not pathway_name:
                    results.append({"error": "Missing 'pathway_name' for get_pathway_id"})
                    continue

                pathway_id, desc = await kegg.get_pathway_id(pathway_name, organism)
                if not pathway_id:
                    results.append({"error": f"No pathway found for: {pathway_name}"})
                    continue

                results.append({
                    "pathway_id": pathway_id,
                    "description": desc
                })

            elif function == "get_pathway_proteins":
                pathway_id = params.get("pathway_id")
                organism = params.get("organism", "hsa")
                if not pathway_id:
                    results.append({"error": "Missing 'pathway_id' for get_pathway_proteins"})
                    continue

                proteins = await kegg.get_pathway_proteins(pathway_id, organism)
                results.append({
                    "pathway_id": pathway_id,
                    "protein_count": len(proteins),
                    "top_proteins": proteins[:5]  # optional
                })

            else:
                results.append({"error": f"Unknown KEGG function: {function}"})

        # Add elif blocks for other APIs like UniProt, ClinVar, etc.

    return results




async def main():
    example_query = "Can you identify proteins involved in apoptosis that are functionally similar to TP53 but are not currently targeted by known drugs"
    plan = generate_bio_plan(example_query)
    print("--- PLAN ---")
    print(json.dumps(plan, indent=2))
    print("\n--- STEP DESCRIPTIONS ---")
    print(explain_personalized_steps(plan))

    print("\n--- EXECUTING PLAN ---")
    results = await execute_bio_plan(plan)
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    asyncio.run(main())

