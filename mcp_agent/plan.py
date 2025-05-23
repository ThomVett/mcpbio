import asyncio

from openai import OpenAI
import json

import kegg
from keys import together_ai_api_key
from prompts import kegg_prompt, Tool, kegg, go_terms, drug_bank

client = OpenAI(api_key=together_ai_api_key, base_url="https://api.together.xyz/v1")


planing_prompt = f"""
You are a biomedical tool planner.

You are given access to a set of bioinformatics Tools. Your job is to:
- Understand the user's question
- Decide which APIs are needed to answer it
- Output a structured JSON plan detailing which API to use, in which order, and what parameters

The tools are defined the following way:

{json.dumps(Tool.model_json_schema())}

Respond ONLY in JSON format like this:

- make sure to 
{{
  "steps": [
    {{
      "tool_name": "tool_name_selected - Tool.name",
      "action": "api_name" (this follows the name defined in APIAccessMethod.function_name) that the Tool has access to),
      "description": "What this step does (in plain English).",
      "params": {{
        "function": "api_function_name_if_applicable",
        "key": "value"
      }}
    }}
  ]
}}

Available tools:


--- 

{json.dumps(kegg.model_dump_json())}

---

{json.dumps(go_terms.model_dump_json())}

---

{json.dumps(drug_bank.model_dump_json())}

"""


empty_string = """

in the first pipeline there are only two steps.

Below are descriptions of available APIs:

---

{kegg_prompt}
"""

STEPS_ENRICHMENT = {
    "clinvar": "This helps understand the medical relevance of the variant.",
    "drugbank": "This could highlight therapeutic opportunities.",
    "uniprot": "This reveals key information about the protein’s role and function.",
    "string": "This helps identify interacting proteins and broader functional networks.",
    "chembl": "This may uncover experimental compounds or drugs under development.",
    "kegg": "This provides insight into the biological pathways the gene participates in.",
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
        if not description.endswith("."):
            description += "."

        extra = STEPS_ENRICHMENT.get(db, "")
        if extra and not extra.endswith("."):
            extra += "."

        final_text = f"**Step {i} – Querying {db_name}**\n{description} {extra}".strip()
        readable_steps.append(final_text)

    return "\n\n".join(readable_steps)


def generate_bio_plan(user_query: str):
    user_prompt = f'User query: "{user_query}"'

    response = client.chat.completions.create(
        model="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",  # Or llama-2-70b-chat, nous-hermes, etc.
        messages=[
            {"role": "system", "content": planing_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=1000,
    )

    output = response.choices[0].message.content

    try:
        # Attempt to find the start of the JSON object
        json_start = output.find("{")
        # Clean up the output by removing any leading or trailing non-JSON content
        cleaned_output = output[json_start:].strip()
        # Attempt to parse the cleaned output as JSON
        return json.loads(cleaned_output)
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

        print("---------------------- first action -----------")
        print(action, params, function)

        if action == "kegg":
            if function == "get_pathway_id":
                pathway_name = params.get("pathway_name")
                organism = params.get("organism", "hsa")
                if not pathway_name:
                    results.append(
                        {"error": "Missing 'pathway_name' for get_pathway_id"}
                    )
                    continue

                pathway_id, desc = await kegg.get_pathway_id(pathway_name, organism)
                if not pathway_id:
                    results.append({"error": f"No pathway found for: {pathway_name}"})
                    continue

                results.append({"pathway_id": pathway_id, "description": desc})

            elif function == "get_pathway_proteins":
                pathway_id = params.get("pathway_id")
                organism = params.get("organism", "hsa")
                if not pathway_id:
                    results.append(
                        {"error": "Missing 'pathway_id' for get_pathway_proteins"}
                    )
                    continue

                proteins = await kegg.get_pathway_proteins(pathway_id, organism)
                results.append(
                    {
                        "pathway_id": pathway_id,
                        "protein_count": len(proteins),
                        "top_proteins": proteins[:5],  # optional
                    }
                )

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
