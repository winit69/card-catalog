import os
import json
import requests
from bs4 import BeautifulSoup
import google.generativeai as genai

# Setup Gemini API (or OpenAI)
genai.configure(api_key=os.environ["GEMINI_API_KEY"])
model = genai.GenerativeModel("gemini-2.5-flash")

# List of target Canadian card directory / listing pages to crawl
TARGET_URLS = [
    "https://www.ratehub.ca/credit-cards/best-credit-cards",
    "https://www.greedyrates.ca/cards/"
]

def fetch_raw_text(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    # Strip unnecessary tags
    for s in soup(['script', 'style', 'nav', 'footer']):
        s.decompose()
    return soup.get_text()[:15000] # Limit window size

def parse_cards_with_ai(raw_text):
    prompt = f"""
    You are a Canadian credit card data expert. Extract all credit cards from the following text.
    Format the response strictly as a JSON array of objects with no markdown codeblocks.

    Output schema for each item:
    {{
      "id": "snake_case_card_id",
      "cardName": "Full Official Card Name",
      "issuer": "Bank or Issuer Name",
      "baseRate": 0.01 (decimal multiplier, e.g. 1% = 0.01),
      "categoryRates": {{
        "groceries": decimal_value,
        "dining": decimal_value,
        "gas": decimal_value,
        "travel": decimal_value,
        "online shopping": decimal_value,
        "other": decimal_value
      }}
    }}

    Raw Text:
    {raw_text}
    """
    
    response = model.generate_content(prompt)
    clean_json = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean_json)

if __name__ == "__main__":
    master_catalog = []
    seen_ids = set()

    for url in TARGET_URLS:
        try:
            print(f"Scraping {url}...")
            raw_text = fetch_raw_text(url)
            cards = parse_cards_with_ai(raw_text)
            
            for card in cards:
                if card['id'] not in seen_ids:
                    seen_ids.add(card['id'])
                    master_catalog.append(card)
        except Exception as e:
            print(f"Error processing {url}: {e}")

    # Write normalized data to cards_catalog.json
    with open("cards_catalog.json", "w", encoding="utf-8") as f:
        json.dump(master_catalog, f, indent=2)

    print(f"Successfully compiled {len(master_catalog)} Canadian credit cards!")
