import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
# FALLBACK SAMPLE DATA
# Used automatically if GST portal is unreachable
# ─────────────────────────────────────────────
SAMPLE_ALERTS = [
    {
        "id": "gst-001",
        "title": "GSTR-3B filing deadline extended to 22nd for small taxpayers",
        "date": "2025-04-28",
        "category": "Filing Deadline",
        "affects": ["restaurant", "kirana", "textile", "pharmacy", "general"],
        "source": "GST Council Notification 12/2025",
        "url": "https://www.gst.gov.in/newsandupdates/read/1234",
        "raw_text": (
            "The GST Council has extended the due date for filing GSTR-3B for taxpayers "
            "with annual aggregate turnover up to Rs.5 crore. The new deadline is the 22nd "
            "of the following month for Category X states and 24th for Category Y states. "
            "This relief applies to quarterly filers under the QRMP scheme."
        ),
        "scraped_at": datetime.now().isoformat(),
        "is_sample": True
    },
    {
        "id": "gst-002",
        "title": "E-invoicing mandatory for businesses above Rs.5 crore turnover",
        "date": "2025-04-20",
        "category": "Compliance Mandate",
        "affects": ["restaurant", "textile", "it_services", "general"],
        "source": "CBIC Circular 04/2025",
        "url": "https://www.gst.gov.in/newsandupdates/read/1235",
        "raw_text": (
            "The Central Board of Indirect Taxes and Customs (CBIC) has notified that "
            "e-invoicing is now mandatory for all registered taxpayers with an aggregate "
            "annual turnover exceeding Rs.5 crore in any preceding financial year. "
            "Businesses must integrate with the Invoice Registration Portal (IRP) before "
            "1st June 2025 or face a penalty of Rs.10,000 per invoice."
        ),
        "scraped_at": datetime.now().isoformat(),
        "is_sample": True
    },
    {
        "id": "gst-003",
        "title": "GST rate on restaurant services inside hotels revised to 18%",
        "date": "2025-04-15",
        "category": "Rate Change",
        "affects": ["restaurant"],
        "source": "GST Council 53rd Meeting Decision",
        "url": "https://www.gst.gov.in/newsandupdates/read/1236",
        "raw_text": (
            "Following the 53rd GST Council meeting, the tax rate on restaurant services "
            "located inside hotels with room tariff exceeding Rs.7,500 per night has been "
            "revised to 18% with Input Tax Credit (ITC) benefit. Standalone restaurants "
            "continue at 5% without ITC. This is effective from 1st May 2025."
        ),
        "scraped_at": datetime.now().isoformat(),
        "is_sample": True
    },
    {
        "id": "gst-004",
        "title": "New HSN code reporting requirements for textile sector from June 2025",
        "date": "2025-04-10",
        "category": "Reporting Requirement",
        "affects": ["textile"],
        "source": "CBIC Notification 08/2025",
        "url": "https://www.gst.gov.in/newsandupdates/read/1237",
        "raw_text": (
            "All textile businesses with turnover above Rs.1.5 crore must mandatorily "
            "report 8-digit HSN codes in GSTR-1 from June 2025. Businesses below this "
            "threshold must report 4-digit HSN codes. Non-compliance will result in "
            "returns being treated as defective and late filing penalties will apply."
        ),
        "scraped_at": datetime.now().isoformat(),
        "is_sample": True
    },
    {
        "id": "gst-005",
        "title": "Input Tax Credit blocked for medicines sold without prescription record",
        "date": "2025-04-05",
        "category": "ITC Rule",
        "affects": ["pharmacy"],
        "source": "CBIC Circular 06/2025",
        "url": "https://www.gst.gov.in/newsandupdates/read/1238",
        "raw_text": (
            "Pharmacies and medical stores must maintain prescription records for Schedule H "
            "and H1 drugs to claim Input Tax Credit on purchases. The CBIC has clarified "
            "that ITC will be blocked under Section 17(5) if sales cannot be traced to "
            "valid prescriptions during audit. Digital records via Mera Aarogya Setu are "
            "accepted as valid proof."
        ),
        "scraped_at": datetime.now().isoformat(),
        "is_sample": True
    },
    {
        "id": "gst-006",
        "title": "Annual Return GSTR-9 filing threshold raised to Rs.2 crore",
        "date": "2025-03-30",
        "category": "Filing Exemption",
        "affects": ["restaurant", "kirana", "textile", "pharmacy", "it_services", "general"],
        "source": "CBIC Notification 10/2025",
        "url": "https://www.gst.gov.in/newsandupdates/read/1239",
        "raw_text": (
            "The government has raised the threshold for mandatory filing of GSTR-9 Annual "
            "Return from Rs.2 crore to Rs.5 crore for FY 2024-25. Taxpayers with annual "
            "aggregate turnover up to Rs.5 crore are exempt from filing GSTR-9 for the "
            "financial year 2024-25. This provides significant relief to small businesses "
            "and reduces their compliance burden."
        ),
        "scraped_at": datetime.now().isoformat(),
        "is_sample": True
    },
    {
        "id": "gst-007",
        "title": "Kirana stores under composition scheme can now sell online",
        "date": "2025-03-22",
        "category": "Policy Change",
        "affects": ["kirana"],
        "source": "GST Council Amendment Notification",
        "url": "https://www.gst.gov.in/newsandupdates/read/1240",
        "raw_text": (
            "Composition scheme taxpayers including small kirana stores are now permitted "
            "to make intra-state supply of goods through e-commerce operators. Earlier, "
            "composition dealers were barred from selling through platforms like Swiggy "
            "Instamart, Blinkit, or Zepto. This change enables small stores to expand "
            "digitally without losing their composition scheme benefits."
        ),
        "scraped_at": datetime.now().isoformat(),
        "is_sample": True
    }
]


# ─────────────────────────────────────────────
# LIVE SCRAPER — attempts to fetch from gst.gov.in
# ─────────────────────────────────────────────

def scrape_gst_portal():
    """
    Attempts to scrape news & updates from the GST portal.
    Returns a list of alert dicts, or None if scraping fails.
    """
    urls_to_try = [
        "https://www.gst.gov.in/newsandupdates",
        "https://tutorial.gst.gov.in/newsandupdates",
    ]

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-IN,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }

    try:
        from bs4 import BeautifulSoup
    except ImportError:
        print("[scraper] BeautifulSoup not found. Run: pip install beautifulsoup4")
        return None

    for url in urls_to_try:
        try:
            print(f"[scraper] Trying: {url}")
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            alerts = []

            # GST portal stores news in a table or list — try multiple selectors
            selectors = [
                "table.table tbody tr",
                ".news-list li",
                ".notification-list li",
                "ul.list-group li",
                ".content-box li",
            ]

            rows = []
            for selector in selectors:
                rows = soup.select(selector)
                if rows:
                    print(f"[scraper] Found {len(rows)} items with selector: {selector}")
                    break

            if not rows:
                # Fallback: grab all anchor tags in the main content area
                content = soup.find("main") or soup.find("div", {"id": "content"}) or soup
                rows = content.find_all("a", href=True)
                print(f"[scraper] Using anchor fallback: {len(rows)} links found")

            for i, row in enumerate(rows[:20]):  # cap at 20 alerts
                try:
                    # Extract text and link
                    text = row.get_text(separator=" ", strip=True)
                    link = row.get("href") or (row.find("a") and row.find("a").get("href")) or ""
                    if not link.startswith("http"):
                        link = "https://www.gst.gov.in" + link

                    # Skip empty or navigation rows
                    if len(text) < 20:
                        continue

                    # Try to parse a date from the row text
                    date_str = datetime.now().strftime("%Y-%m-%d")

                    alert = {
                        "id": f"gst-live-{i+1:03d}",
                        "title": text[:200],
                        "date": date_str,
                        "category": "GST Update",
                        "affects": ["general"],
                        "source": "gst.gov.in",
                        "url": link,
                        "raw_text": text,
                        "scraped_at": datetime.now().isoformat(),
                        "is_sample": False
                    }
                    alerts.append(alert)

                except Exception as e:
                    print(f"[scraper] Skipping row {i}: {e}")
                    continue

            if alerts:
                print(f"[scraper] Successfully scraped {len(alerts)} alerts.")
                return alerts
            else:
                print(f"[scraper] No alerts parsed from {url}. Trying next URL...")

        except requests.exceptions.Timeout:
            print(f"[scraper] Timeout on {url}")
        except requests.exceptions.ConnectionError:
            print(f"[scraper] Connection error on {url} — portal may be blocking scrapers")
        except requests.exceptions.HTTPError as e:
            print(f"[scraper] HTTP error {e} on {url}")
        except Exception as e:
            print(f"[scraper] Unexpected error on {url}: {e}")

    return None  # all URLs failed


# ─────────────────────────────────────────────
# SAVE TO JSON
# ─────────────────────────────────────────────

def save_alerts(alerts, filepath="alerts.json"):
    """Saves the alerts list to a JSON file."""
    output = {
        "last_updated": datetime.now().isoformat(),
        "total": len(alerts),
        "alerts": alerts
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"[scraper] Saved {len(alerts)} alerts → {filepath}")


def load_alerts(filepath="alerts.json"):
    """Loads alerts from the saved JSON file."""
    if not os.path.exists(filepath):
        return []
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("alerts", [])


# ─────────────────────────────────────────────
# MAIN — run this file directly
# ─────────────────────────────────────────────

def run_scraper():
    print("=" * 50)
    print("RegRadar GST Alert Scraper")
    print("=" * 50)

    # 1. Try live scraping first
    print("\n[scraper] Attempting live scrape from gst.gov.in...")
    live_alerts = scrape_gst_portal()

    if live_alerts:
        print(f"[scraper] Live data retrieved: {len(live_alerts)} alerts")
        alerts = live_alerts
    else:
        # 2. Fall back to sample data
        print("\n[scraper] Live scrape failed or returned no data.")
        print("[scraper] Using sample data for demo purposes.")
        print("[scraper] (This is normal — gst.gov.in blocks automated requests)")
        alerts = SAMPLE_ALERTS

    # 3. Save to file
    save_alerts(alerts)

    # 4. Preview first 3 alerts
    print("\n── Preview of first 3 alerts ──")
    for alert in alerts[:3]:
        source_tag = "[LIVE]" if not alert.get("is_sample") else "[SAMPLE]"
        print(f"\n{source_tag} {alert['title']}")
        print(f"   Date     : {alert['date']}")
        print(f"   Category : {alert['category']}")
        print(f"   Affects  : {', '.join(alert['affects'])}")
        print(f"   URL      : {alert['url']}")

    print("\n[scraper] Done. alerts.json is ready for the AI engine.")
    return alerts


if __name__ == "__main__":
    run_scraper()
