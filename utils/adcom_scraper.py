"""
Advisory Committee Materials Scraper

Scrapes advisory committee meeting materials from FDA website.
Downloads PDF links, meeting dates, committee names, and document titles.
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Any
import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

def fetch_advisory_committee_calendar() -> Dict[str, Any]:
    """
    Fetch the advisory committee calendar JSON from FDA website.

    Returns:
        Dictionary containing:
        {
            "success": bool,
            "meetings": List[Dict] - list of meeting entries,
            "total_count": int
        }
    """
    url = "https://www.fda.gov/datatables-json/advisory-committee-calendar-json"

    headers = {
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'en-US,en;q=0.9',
        'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest'
    }

    try:
        logger.info("Fetching advisory committee calendar JSON")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        data = response.json()

        return {
            "success": True,
            "meetings": data if isinstance(data, list) else [],
            "total_count": len(data) if isinstance(data, list) else 0
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching calendar: {e}")
        return {
            "success": False,
            "error": f"Request error: {str(e)}",
            "meetings": [],
            "total_count": 0
        }
    except Exception as e:
        logger.error(f"Error fetching calendar: {e}")
        return {
            "success": False,
            "error": str(e),
            "meetings": [],
            "total_count": 0
        }

def extract_meeting_url(title_html: str) -> str:
    """
    Extract the meeting URL from the HTML title field.

    Args:
        title_html: HTML string containing the link

    Returns:
        Relative URL path (e.g., "/advisory-committees/...")
    """
    soup = BeautifulSoup(title_html, 'html.parser')
    link = soup.find('a')

    if link and link.get('href'):
        return link.get('href')

    return ""

def scrape_meeting_materials(meeting_url: str) -> Dict[str, Any]:
    """
    Scrape a specific meeting page for PDF materials.

    Args:
        meeting_url: Relative URL path to the meeting page

    Returns:
        Dictionary containing:
        {
            "success": bool,
            "meeting_url": str,
            "materials": List[Dict] - list of PDF materials with metadata
        }
    """
    base_url = "https://www.fda.gov"
    full_url = base_url + meeting_url if meeting_url.startswith('/') else meeting_url

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'accept-language': 'en-US,en;q=0.9',
        'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36'
    }

    try:
        logger.info(f"Scraping meeting materials from {full_url}")
        response = requests.get(full_url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        materials = []

        # Find table and all rows
        table = soup.find('table')
        if not table:
            logger.warning("No table found on meeting page")
            return {
                "success": True,
                "meeting_url": full_url,
                "materials": materials
            }

        rows = table.find_all('tr')

        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 2:
                continue

            # First cell contains the link and title
            link_cell = cells[0]
            link = link_cell.find('a', href=True)

            if not link:
                continue

            href = link.get('href', '')
            title = link.get_text(strip=True)

            # Second cell contains file type and size
            file_info_cell = cells[1]
            file_info = file_info_cell.get_text(strip=True).lower()

            # Only collect PDFs
            if 'pdf' not in file_info:
                continue

            # Extract file size
            file_size = ""
            size_match = re.search(r'\((.*?)\)', file_info)
            if size_match:
                file_size = size_match.group(1)

            # Third cell contains source (if exists)
            source = ""
            if len(cells) > 2:
                source = cells[2].get_text(strip=True)

            # Build full PDF URL
            pdf_url = base_url + href if href.startswith('/') else href

            material = {
                "title": title,
                "pdf_url": pdf_url,
                "file_size": file_size,
                "source": source
            }

            materials.append(material)

        logger.info(f"Found {len(materials)} PDF materials")

        return {
            "success": True,
            "meeting_url": full_url,
            "materials": materials
        }

    except requests.exceptions.RequestException as e:
        logger.error(f"Request error scraping materials: {e}")
        return {
            "success": False,
            "error": f"Request error: {str(e)}",
            "meeting_url": full_url,
            "materials": []
        }
    except Exception as e:
        logger.error(f"Error scraping materials: {e}")
        return {
            "success": False,
            "error": str(e),
            "meeting_url": full_url,
            "materials": []
        }

def parse_meeting_date(date_str: str) -> str:
    """
    Parse meeting date string to ISO format.

    Args:
        date_str: Date string like "02/25/2016 03:00 AM EST"

    Returns:
        ISO format date string (YYYY-MM-DD) or original if parsing fails
    """
    try:
        # Extract just the date part (MM/DD/YYYY)
        date_part = date_str.split()[0]
        dt = datetime.strptime(date_part, "%m/%d/%Y")
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return date_str

def search_advisory_committee_materials(
    committee: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Search for advisory committee meeting materials.

    Args:
        committee: Committee name to filter (case-insensitive partial match)
        start_date: Filter meetings on or after this date (YYYY-MM-DD or MM/DD/YYYY)
        end_date: Filter meetings on or before this date (YYYY-MM-DD or MM/DD/YYYY)
        limit: Maximum number of meetings to process (default: 100)

    Returns:
        Dictionary containing:
        {
            "success": bool,
            "query": dict of search parameters,
            "total_meetings": int,
            "meetings": List[Dict] - meetings with their materials
        }
    """
    # Fetch calendar
    calendar_result = fetch_advisory_committee_calendar()

    if not calendar_result["success"]:
        return calendar_result

    meetings = calendar_result["meetings"]

    # Apply filters
    filtered_meetings = []

    for meeting in meetings:
        # Filter by committee
        if committee:
            center = meeting.get("field_center", "").lower()
            title = meeting.get("title", "").lower()
            if committee.lower() not in center and committee.lower() not in title:
                continue

        # Filter by date range
        meeting_date_str = meeting.get("field_start_date", "")
        meeting_date = parse_meeting_date(meeting_date_str)

        if start_date:
            if meeting_date < start_date:
                continue

        if end_date:
            if meeting_date > end_date:
                continue

        filtered_meetings.append(meeting)

        if len(filtered_meetings) >= limit:
            break

    # Process each meeting to get materials
    results = []

    for meeting in filtered_meetings:
        title_html = meeting.get("title", "")
        meeting_url = extract_meeting_url(title_html)

        if not meeting_url:
            continue

        # Extract meeting info
        soup = BeautifulSoup(title_html, 'html.parser')
        meeting_title = soup.get_text(strip=True)

        # Scrape materials
        materials_result = scrape_meeting_materials(meeting_url)

        if not materials_result["success"]:
            continue

        # Build result entry
        result = {
            "date": parse_meeting_date(meeting.get("field_start_date", "")),
            "committee": meeting.get("field_center", ""),
            "title": meeting_title,
            "meeting_url": materials_result["meeting_url"],
            "materials": materials_result["materials"]
        }

        results.append(result)

    return {
        "success": True,
        "query": {
            "committee": committee,
            "start_date": start_date,
            "end_date": end_date,
            "limit": limit
        },
        "total_meetings": len(results),
        "meetings": results
    }
