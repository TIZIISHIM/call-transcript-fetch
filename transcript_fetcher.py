"""
Earnings Call Transcript Fetcher & Parser
Fetches transcripts from Seeking Alpha and extracts prepared remarks.
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime
from typing import Optional, Dict, List
import time

class TranscriptFetcher:
    """Fetch and parse earnings call transcripts from Seeking Alpha."""
    
    def __init__(self):
        self.base_url = "https://seekingalpha.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def search_transcript(self, ticker: str, year: int, quarter: int) -> Optional[Dict]:
        """
        Search for a specific earnings call transcript.
        
        Args:
            ticker: Stock ticker (e.g., 'NVDA')
            year: Year of earnings call
            quarter: Quarter number (1, 2, 3, 4)
            
        Returns:
            Dictionary with transcript data or None if not found
        """
        # Construct search URL
        search_url = f"{self.base_url}/search?q={ticker}%20{year}%20Q{quarter}%20earnings%20call%20transcript"
        
        try:
            response = requests.get(search_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find transcript link (simplified - real implementation would need robust selectors)
            # For demonstration, we'll use a pattern match
            transcript_links = soup.find_all('a', href=re.compile(r'/article/.*-earnings-call-transcript'))
            
            if not transcript_links:
                return None
                
            transcript_url = transcript_links[0]['href']
            if not transcript_url.startswith('http'):
                transcript_url = self.base_url + transcript_url
                
            return self.parse_transcript(transcript_url, ticker, year, quarter)
            
        except Exception as e:
            print(f"Error searching for {ticker} Q{quarter} {year}: {e}")
            return None
    
    def parse_transcript(self, url: str, ticker: str, year: int, quarter: int) -> Dict:
        """
        Parse a transcript page and extract prepared remarks.
        
        Args:
            url: Full URL of the transcript page
            ticker: Stock ticker
            year: Year of earnings call
            quarter: Quarter number
            
        Returns:
            Structured transcript data
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the transcript body
            # This is simplified - real implementation would need to handle various formats
            transcript_text = ""
            
            # Look for common transcript containers
            for container in soup.find_all(['div', 'article'], class_=re.compile(r'transcript|article-content')):
                transcript_text = container.get_text()
                if len(transcript_text) > 1000:  # Found substantial content
                    break
            
            # Extract prepared remarks (between "Prepared Remarks" and "Questions and Answers")
            prepared_remarks = self._extract_prepared_remarks(transcript_text)
            
            return {
                'ticker': ticker,
                'year': year,
                'quarter': quarter,
                'url': url,
                'fetched_at': datetime.now().isoformat(),
                'prepared_remarks': prepared_remarks,
                'full_text': transcript_text[:5000]  # Truncate for storage
            }
            
        except Exception as e:
            print(f"Error parsing transcript {url}: {e}")
            return None
    
    def _extract_prepared_remarks(self, text: str) -> str:
        """Extract the prepared remarks section from full transcript text."""
        # Look for common section markers
        patterns = [
            (r'Prepared Remarks(.*?)Questions and Answers', re.DOTALL | re.IGNORECASE),
            (r'Operator(.*?)Thank you', re.DOTALL | re.IGNORECASE),
            (r'Opening Remarks(.*?)Q&A', re.DOTALL | re.IGNORECASE)
        ]
        
        for pattern, flags in patterns:
            match = re.search(pattern, text, flags)
            if match:
                remarks = match.group(1).strip()
                # Clean up extra whitespace
                remarks = re.sub(r'\n\s*\n', '\n\n', remarks)
                return remarks[:3000]  # Limit length
        
        # If no section markers found, return first 2000 characters
        return text[:2000]
    
    def compare_transcripts(self, ticker: str, 
                           current_year: int, current_quarter: int,
                           previous_year: int, previous_quarter: int) -> Dict:
        """
        Compare two transcripts and return changes.
        
        This is a simplified comparison - production version would use difflib.
        """
        current = self.search_transcript(ticker, current_year, current_quarter)
        time.sleep(1)  # Be respectful to the source
        previous = self.search_transcript(ticker, previous_year, previous_quarter)
        
        if not current or not previous:
            return {'error': 'One or both transcripts not found'}
        
        return {
            'ticker': ticker,
            'current': {
                'quarter': f"Q{current_quarter} {current_year}",
                'prepared_remarks_excerpt': current['prepared_remarks'][:500]
            },
            'previous': {
                'quarter': f"Q{previous_quarter} {previous_year}",
                'prepared_remarks_excerpt': previous['prepared_remarks'][:500]
            },
            'comparison_available': True
        }


# Example usage
if __name__ == "__main__":
    fetcher = TranscriptFetcher()
    
    # Compare NVDA Q3 vs Q2 2024
    result = fetcher.compare_transcripts('NVDA', 2024, 3, 2024, 2)
    print(json.dumps(result, indent=2))
