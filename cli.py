"""
CLI interface for NAMASTE-ICD11 Terminology Service
Simple command-line tool for searching and translating codes
"""

import asyncio
import httpx
import sys
import json
from typing import Optional


API_BASE = "http://localhost:8000"
TOKEN = "demo-token-12345"


async def search(query: str, system: Optional[str] = None):
    """Search for diagnoses"""
    async with httpx.AsyncClient() as client:
        params = {"query": query, "limit": 10}
        if system:
            params["system"] = system
        
        headers = {"Authorization": f"Bearer {TOKEN}"}
        response = await client.get(f"{API_BASE}/api/search", params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nFound {len(data['results'])} results:\n")
            for result in data['results']:
                print(f"  Code: {result['code']}")
                print(f"  Display: {result['display']}")
                print(f"  System: {result['system_name']}")
                if result.get('definition'):
                    print(f"  Definition: {result['definition']}")
                print()
        else:
            print(f"Error: {response.status_code} - {response.text}")


async def translate(source_code: str, source_system: str, target_system: str):
    """Translate codes between systems"""
    async with httpx.AsyncClient() as client:
        params = {
            "source_code": source_code,
            "source_system": source_system,
            "target_system": target_system
        }
        headers = {"Authorization": f"Bearer {TOKEN}"}
        response = await client.post(f"{API_BASE}/api/translate", params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nTranslation Result:")
            print(f"  Source: {data['source_code']} ({data['source_system']})")
            print(f"  Target System: {data['target_system']}")
            print(f"  Target Codes: {', '.join(data['target_codes'])}")
            print(f"  Equivalence: {data['equivalence']}\n")
        else:
            print(f"Error: {response.status_code} - {response.text}")


async def lookup_icd11(code: Optional[str] = None, query: Optional[str] = None):
    """Lookup ICD-11 Biomedicine codes"""
    async with httpx.AsyncClient() as client:
        params = {}
        if code:
            params["code"] = code
        elif query:
            params["query"] = query
        else:
            print("Error: Either 'code' or 'query' parameter required")
            return
        
        headers = {"Authorization": f"Bearer {TOKEN}"}
        response = await client.get(f"{API_BASE}/api/icd11/biomedicine", params=params, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                print(f"\nFound {len(data)} results:\n")
                for item in data:
                    print(f"  Code: {item['code']}")
                    print(f"  Display: {item['display']}")
                    if item.get('definition'):
                        print(f"  Definition: {item['definition']}")
                    print()
            else:
                print(f"\nICD-11 Code:")
                print(f"  Code: {data['code']}")
                print(f"  Display: {data['display']}")
                if data.get('definition'):
                    print(f"  Definition: {data['definition']}")
                print()
        else:
            print(f"Error: {response.status_code} - {response.text}")


async def get_codesystem(system: str):
    """Get FHIR CodeSystem"""
    async with httpx.AsyncClient() as client:
        url_map = {
            "namaste": f"{API_BASE}/fhir/CodeSystem/namaste",
            "tm2": f"{API_BASE}/fhir/CodeSystem/icd11-tm2",
            "biomedicine": f"{API_BASE}/fhir/CodeSystem/icd11-biomedicine"
        }
        
        if system not in url_map:
            print(f"Error: Unknown system '{system}'. Use: namaste, tm2, or biomedicine")
            return
        
        response = await client.get(url_map[system])
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n{data.get('title', 'CodeSystem')}:")
            print(f"  URL: {data.get('url')}")
            print(f"  Version: {data.get('version')}")
            print(f"  Concepts: {len(data.get('concept', []))}\n")
        else:
            print(f"Error: {response.status_code} - {response.text}")


def print_usage():
    """Print usage information"""
    print("""
NAMASTE-ICD11 Terminology Service CLI

Usage:
  python cli.py search <query> [--system SYSTEM]
  python cli.py translate <source_code> <source_system> <target_system>
  python cli.py lookup-icd11 [--code CODE | --query QUERY]
  python cli.py codesystem <system>

Examples:
  python cli.py search "Jwara"
  python cli.py search "Fever" --system NAMASTE
  python cli.py translate NAMASTE-001 NAMASTE ICD11-TM2
  python cli.py lookup-icd11 --code AB30
  python cli.py lookup-icd11 --query "fever"
  python cli.py codesystem namaste
""")


async def main():
    """Main CLI entry point"""
    if len(sys.argv) < 2:
        print_usage()
        return
    
    command = sys.argv[1]
    
    try:
        if command == "search":
            query = sys.argv[2] if len(sys.argv) > 2 else None
            system = sys.argv[sys.argv.index("--system") + 1] if "--system" in sys.argv else None
            if not query:
                print("Error: Query required")
                return
            await search(query, system)
        
        elif command == "translate":
            if len(sys.argv) < 5:
                print("Error: translate requires source_code, source_system, and target_system")
                return
            await translate(sys.argv[2], sys.argv[3], sys.argv[4])
        
        elif command == "lookup-icd11":
            code = None
            query = None
            if "--code" in sys.argv:
                code = sys.argv[sys.argv.index("--code") + 1]
            elif "--query" in sys.argv:
                query = sys.argv[sys.argv.index("--query") + 1]
            await lookup_icd11(code, query)
        
        elif command == "codesystem":
            if len(sys.argv) < 3:
                print("Error: codesystem requires system name")
                return
            await get_codesystem(sys.argv[2])
        
        else:
            print_usage()
    
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
