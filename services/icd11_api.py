import httpx
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ICD11API:
    """
    Service to interact with the public ICD-11 API (via NIH Clinical Tables).
    Base URL: https://clinicaltables.nlm.nih.gov/api/icd11_codes/v3/search
    """
    
    BASE_URL = "https://clinicaltables.nlm.nih.gov/api/icd11_codes/v3/search"

    async def search(self, term: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for ICD-11 codes using the NIH API.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    self.BASE_URL,
                    params={
                        "terms": term,
                        "maxList": max_results,
                        "df": "code,title,browserUrl" # Display fields
                    }
                )
                
                if response.status_code == 200:
                    # Response format: [total, codes, extra, display_list, ...]
                    # display_list is [[code, title, url], ...]
                    data = response.json()
                    if len(data) >= 4:
                        results = []
                        display_list = data[3]
                        for item in display_list:
                            results.append({
                                "code": item[0],
                                "title": item[1],
                                "url": item[2] if len(item) > 2 else ""
                            })
                        return results
                else:
                    logger.error(f"ICD-11 API Error: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"ICD-11 API Exception: {e}")
            return []
        
        return []
