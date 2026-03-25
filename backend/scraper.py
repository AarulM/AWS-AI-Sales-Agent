import requests
from bs4 import BeautifulSoup
from typing import List, Dict
import re
from urllib.parse import urljoin, urlparse

class WebScraper:
    """Scrapes website content for knowledge base"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def scrape_website(self, url: str, max_pages: int = 10) -> Dict:
        """
        Scrape a website and extract knowledge
        
        Args:
            url: Website URL to scrape
            max_pages: Maximum number of pages to scrape
            
        Returns:
            Dict with scraped content organized by category
        """
        # Validate and fix URL
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        print(f"🕷️  Starting scrape of: {url}")
        
        knowledge = {
            "business_info": {},
            "services": [],
            "pricing": [],
            "faqs": [],
            "contact": {},
            "about": "",
            "raw_content": []
        }
        
        try:
            # Scrape main page
            main_content = self._scrape_page(url)
            if not main_content:
                return knowledge
            
            # Extract structured information
            knowledge["business_info"] = self._extract_business_info(main_content, url)
            knowledge["services"] = self._extract_services(main_content)
            knowledge["pricing"] = self._extract_pricing(main_content)
            knowledge["faqs"] = self._extract_faqs(main_content)
            knowledge["contact"] = self._extract_contact_info(main_content)
            knowledge["about"] = self._extract_about(main_content)
            
            # Get all text content
            knowledge["raw_content"] = self._extract_text_chunks(main_content)
            
            print(f"✅ Scraped {len(knowledge['services'])} services, {len(knowledge['faqs'])} FAQs")
            
        except Exception as e:
            print(f"❌ Scraping error: {e}")
        
        return knowledge
    
    def _scrape_page(self, url: str) -> BeautifulSoup:
        """Scrape a single page"""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"❌ Error scraping {url}: {e}")
            return None
    
    def _extract_business_info(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract business name and basic info"""
        info = {
            "name": "",
            "domain": urlparse(url).netloc,
            "url": url
        }
        
        # Try to get business name from title or h1
        title = soup.find('title')
        if title:
            info["name"] = title.get_text().strip()
        
        h1 = soup.find('h1')
        if h1 and not info["name"]:
            info["name"] = h1.get_text().strip()
        
        return info
    
    def _extract_services(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract services/products"""
        services = []
        
        # Look for common service section patterns
        service_keywords = ['service', 'product', 'offering', 'solution', 'what we do']
        
        # Find sections with service keywords
        for keyword in service_keywords:
            sections = soup.find_all(['section', 'div'], class_=re.compile(keyword, re.I))
            sections += soup.find_all(['section', 'div'], id=re.compile(keyword, re.I))
            
            for section in sections:
                # Find service items (usually in lists or cards)
                items = section.find_all(['li', 'div', 'article'])
                
                for item in items[:10]:  # Limit to 10 services
                    title_elem = item.find(['h2', 'h3', 'h4', 'strong'])
                    desc_elem = item.find(['p', 'span'])
                    
                    if title_elem:
                        service = {
                            "title": title_elem.get_text().strip(),
                            "description": desc_elem.get_text().strip() if desc_elem else ""
                        }
                        if service["title"] and len(service["title"]) < 100:
                            services.append(service)
        
        # Remove duplicates
        seen = set()
        unique_services = []
        for service in services:
            if service["title"] not in seen:
                seen.add(service["title"])
                unique_services.append(service)
        
        return unique_services[:10]  # Return top 10
    
    def _extract_pricing(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract pricing information"""
        pricing = []
        
        # Look for pricing sections
        price_sections = soup.find_all(['section', 'div'], class_=re.compile('pric', re.I))
        price_sections += soup.find_all(['section', 'div'], id=re.compile('pric', re.I))
        
        for section in price_sections:
            # Find price elements
            prices = section.find_all(text=re.compile(r'\$\d+'))
            
            for price_text in prices[:5]:
                parent = price_text.parent
                context = parent.get_text().strip()
                
                if len(context) < 200:
                    pricing.append({
                        "text": context,
                        "price": re.search(r'\$\d+(?:,\d{3})*(?:\.\d{2})?', context).group()
                    })
        
        return pricing
    
    def _extract_faqs(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract FAQ items"""
        faqs = []
        
        # Look for FAQ sections
        faq_sections = soup.find_all(['section', 'div'], class_=re.compile('faq', re.I))
        faq_sections += soup.find_all(['section', 'div'], id=re.compile('faq', re.I))
        
        for section in faq_sections:
            # Find Q&A pairs
            questions = section.find_all(['h2', 'h3', 'h4', 'dt', 'strong'])
            
            for q in questions[:10]:
                question_text = q.get_text().strip()
                
                # Find answer (usually next sibling or parent's next sibling)
                answer_elem = q.find_next_sibling(['p', 'dd', 'div'])
                answer_text = answer_elem.get_text().strip() if answer_elem else ""
                
                if question_text and len(question_text) < 200:
                    faqs.append({
                        "question": question_text,
                        "answer": answer_text
                    })
        
        return faqs
    
    def _extract_contact_info(self, soup: BeautifulSoup) -> Dict:
        """Extract contact information"""
        contact = {
            "phone": "",
            "email": "",
            "address": ""
        }
        
        text = soup.get_text()
        
        # Extract phone
        phone_match = re.search(r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
        if phone_match:
            contact["phone"] = phone_match.group()
        
        # Extract email
        email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
        if email_match:
            contact["email"] = email_match.group()
        
        return contact
    
    def _extract_about(self, soup: BeautifulSoup) -> str:
        """Extract about/description"""
        about_sections = soup.find_all(['section', 'div'], class_=re.compile('about', re.I))
        about_sections += soup.find_all(['section', 'div'], id=re.compile('about', re.I))
        
        if about_sections:
            return about_sections[0].get_text().strip()[:500]
        
        # Fallback to meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            return meta_desc.get('content', '')
        
        return ""
    
    def _extract_text_chunks(self, soup: BeautifulSoup) -> List[str]:
        """Extract all meaningful text in chunks"""
        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'footer', 'header']):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean up
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Split into chunks of ~500 characters
        chunk_size = 500
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunk = text[i:i+chunk_size]
            if len(chunk) > 100:  # Only keep substantial chunks
                chunks.append(chunk)
        
        return chunks[:20]  # Limit to 20 chunks
    
    def format_for_knowledge_base(self, scraped_data: Dict, client_id: str) -> List[Dict]:
        """Format scraped data into knowledge base items"""
        knowledge_items = []
        
        # Business info
        if scraped_data["business_info"].get("name"):
            knowledge_items.append({
                "category": "company",
                "title": "Business Information",
                "content": f"Business: {scraped_data['business_info']['name']}. Website: {scraped_data['business_info']['url']}",
                "tags": ["company", "business", "info"]
            })
        
        # Services
        for service in scraped_data["services"]:
            knowledge_items.append({
                "category": "services",
                "title": service["title"],
                "content": service["description"] or service["title"],
                "tags": ["service", "offering"]
            })
        
        # Pricing
        for price in scraped_data["pricing"]:
            knowledge_items.append({
                "category": "pricing",
                "title": f"Pricing: {price['price']}",
                "content": price["text"],
                "tags": ["pricing", "cost", "rate"]
            })
        
        # FAQs
        for faq in scraped_data["faqs"]:
            knowledge_items.append({
                "category": "faqs",
                "title": faq["question"],
                "content": faq["answer"],
                "tags": ["faq", "question"]
            })
        
        # Contact
        if scraped_data["contact"].get("phone") or scraped_data["contact"].get("email"):
            content = []
            if scraped_data["contact"].get("phone"):
                content.append(f"Phone: {scraped_data['contact']['phone']}")
            if scraped_data["contact"].get("email"):
                content.append(f"Email: {scraped_data['contact']['email']}")
            
            knowledge_items.append({
                "category": "contact",
                "title": "Contact Information",
                "content": ". ".join(content),
                "tags": ["contact", "phone", "email"]
            })
        
        # About
        if scraped_data["about"]:
            knowledge_items.append({
                "category": "company",
                "title": "About Us",
                "content": scraped_data["about"],
                "tags": ["about", "company", "description"]
            })
        
        return knowledge_items
