import asyncio
from weather import get_alerts, get_forecast, kegg_pathway_proteins
import kegg


async def test_kegg_pathway_tool():
    # Test the MCP tool
    result = await kegg_pathway_proteins("apoptosis")
    print("--- MCP TOOL RESULT ---")
    print(result)
    print("\n")


async def test_kegg_functions():
    # Test the individual kegg functions
    print("--- INDIVIDUAL KEGG FUNCTIONS ---")

    # Test pathway ID lookup
    pathway_id, pathway_desc = await kegg.get_pathway_id("apoptosis")
    print(f"Pathway ID: {pathway_id}, Description: {pathway_desc}")

    if pathway_id:
        # Test pathway proteins
        proteins = await kegg.get_pathway_proteins(pathway_id)
        print(f"Found {len(proteins)} proteins")

        # Print first 5 proteins
        for i, protein in enumerate(proteins[:5]):
            print(f"{protein['id']}: {protein.get('name', 'No name')}")
            if i >= 4:
                print("...")


async def test_get_alerts():
    # Test the get_alerts function
    result = await get_alerts("CA")  # California
    print(result)


async def test_get_forecast():
    # Test the get_forecast function
    # San Francisco coordinates
    result = await get_forecast(37.7749, -122.4194)
    print(result)


async def main():
    # Choose which function to test by uncommenting one of these lines
    await test_kegg_pathway_tool()
    await test_kegg_functions()
    # await test_get_alerts()
    # await test_get_forecast()


if __name__ == "__main__":
    asyncio.run(main())