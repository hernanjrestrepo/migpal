"""
MigPAL Housing Scraper - Scraping de Viviendas
Scraping directo de Zillow, Apartments.com, Realtor.com

SIN APIs DE PAGO - Solo scraping directo
"""

import json
import re
import random
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import asyncio

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# User agents rotativos para evitar bloqueos
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


@dataclass
class HousingListing:
    """Listado de vivienda"""
    id: str
    source: str  # zillow, apartments, realtor
    address: str
    city: str
    state: str
    zip_code: str = ""
    
    price: int = 0
    beds: int = 0
    baths: float = 0
    sqft: int = 0
    
    property_type: str = ""  # apartment, house, condo, townhouse
    listing_type: str = "rent"  # rent, sale
    
    photo_url: str = ""
    detail_url: str = ""
    
    amenities: List[str] = field(default_factory=list)
    description: str = ""
    
    lat: float = 0.0
    lng: float = 0.0
    
    posted_date: str = ""
    available_date: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "source": self.source,
            "address": self.address,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "price": self.price,
            "beds": self.beds,
            "baths": self.baths,
            "sqft": self.sqft,
            "property_type": self.property_type,
            "listing_type": self.listing_type,
            "photo_url": self.photo_url,
            "detail_url": self.detail_url,
            "amenities": self.amenities,
            "description": self.description,
            "lat": self.lat,
            "lng": self.lng,
        }


class HousingScraper:
    """Scraper de viviendas multi-fuente"""
    
    def __init__(self):
        self.cache: Dict[str, List[HousingListing]] = {}
        self.cache_time: Dict[str, datetime] = {}
        self.cache_duration = 3600  # 1 hora
    
    def _get_headers(self) -> Dict[str, str]:
        """Genera headers con user agent aleatorio"""
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }
    
    def _is_cache_valid(self, key: str) -> bool:
        """Verifica si el cache es válido"""
        if key not in self.cache_time:
            return False
        elapsed = (datetime.now() - self.cache_time[key]).total_seconds()
        return elapsed < self.cache_duration
    
    async def search_rentals(
        self,
        city: str,
        state: str,
        min_price: int = 0,
        max_price: int = 10000,
        beds: int = 0,
        limit: int = 20
    ) -> List[HousingListing]:
        """Busca rentals en múltiples fuentes"""
        cache_key = f"{city}_{state}_{min_price}_{max_price}_{beds}"
        
        if self._is_cache_valid(cache_key):
            return self.cache[cache_key][:limit]
        
        all_listings = []
        
        # Intentar Zillow
        try:
            zillow_listings = await self._scrape_zillow(city, state, "rent", min_price, max_price, beds)
            all_listings.extend(zillow_listings)
            logger.info(f"Zillow: {len(zillow_listings)} listings")
        except Exception as e:
            logger.error(f"Zillow scrape error: {e}")
        
        # Intentar Apartments.com
        try:
            apartments_listings = await self._scrape_apartments_com(city, state, min_price, max_price, beds)
            all_listings.extend(apartments_listings)
            logger.info(f"Apartments.com: {len(apartments_listings)} listings")
        except Exception as e:
            logger.error(f"Apartments.com scrape error: {e}")
        
        # Ordenar por precio
        all_listings.sort(key=lambda x: x.price if x.price else 999999)
        
        # Guardar en cache
        self.cache[cache_key] = all_listings
        self.cache_time[cache_key] = datetime.now()
        
        return all_listings[:limit]
    
    async def _scrape_zillow(
        self,
        city: str,
        state: str,
        listing_type: str = "rent",
        min_price: int = 0,
        max_price: int = 10000,
        beds: int = 0
    ) -> List[HousingListing]:
        """Scrape Zillow"""
        listings = []
        
        # Formatear URL
        city_slug = city.lower().replace(" ", "-")
        state_slug = state.lower()
        
        if listing_type == "rent":
            url = f"https://www.zillow.com/{city_slug}-{state_slug}/rentals/"
        else:
            url = f"https://www.zillow.com/{city_slug}-{state_slug}/"
        
        # Agregar filtros
        params = []
        if min_price > 0:
            params.append(f"price%2F{min_price}_")
        if max_price < 10000:
            params.append(f"_{max_price}")
        if beds > 0:
            params.append(f"{beds}-_beds")
        
        if params:
            url += "?" + "&".join(params)
        
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url, headers=self._get_headers())
                
                if response.status_code != 200:
                    logger.warning(f"Zillow returned {response.status_code}")
                    return listings
                
                html = response.text
                
                # Buscar datos JSON en el HTML
                # Zillow guarda los datos en un script con __NEXT_DATA__ o searchPageState
                
                # Método 1: Buscar __NEXT_DATA__
                next_data_match = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.+?)</script>', html, re.DOTALL)
                if next_data_match:
                    try:
                        data = json.loads(next_data_match.group(1))
                        search_results = self._extract_zillow_next_data(data)
                        listings.extend(search_results)
                    except json.JSONDecodeError:
                        pass
                
                # Método 2: Buscar en scripts con searchPageState
                if not listings:
                    soup = BeautifulSoup(html, "html.parser")
                    scripts = soup.find_all("script")
                    
                    for script in scripts:
                        text = script.string or ""
                        if "listResults" in text or "searchResults" in text:
                            # Intentar extraer JSON
                            json_match = re.search(r'\{.*"listResults".*\}', text, re.DOTALL)
                            if json_match:
                                try:
                                    data = json.loads(json_match.group())
                                    results = data.get("cat1", {}).get("searchResults", {}).get("listResults", [])
                                    if not results:
                                        results = data.get("searchResults", {}).get("listResults", [])
                                    
                                    for item in results:
                                        listing = self._parse_zillow_item(item, city, state)
                                        if listing:
                                            listings.append(listing)
                                except:
                                    pass
                
                # Método 3: Parsear HTML directamente
                if not listings:
                    listings = self._parse_zillow_html(html, city, state)
        
        except Exception as e:
            logger.error(f"Zillow scrape exception: {e}")
        
        return listings
    
    def _extract_zillow_next_data(self, data: Dict) -> List[HousingListing]:
        """Extrae listings de __NEXT_DATA__"""
        listings = []
        
        try:
            # Navegar la estructura de Next.js
            props = data.get("props", {})
            page_props = props.get("pageProps", {})
            search_page_state = page_props.get("searchPageState", {})
            cat1 = search_page_state.get("cat1", {})
            search_results = cat1.get("searchResults", {})
            list_results = search_results.get("listResults", [])
            
            for item in list_results:
                listing = self._parse_zillow_item(item, "", "")
                if listing:
                    listings.append(listing)
        except Exception as e:
            logger.error(f"Error extracting Zillow next data: {e}")
        
        return listings
    
    def _parse_zillow_item(self, item: Dict, city: str, state: str) -> Optional[HousingListing]:
        """Parsea un item de Zillow"""
        try:
            zpid = item.get("zpid") or item.get("id") or str(random.randint(100000, 999999))
            
            # Extraer precio
            price = item.get("unformattedPrice") or item.get("price") or 0
            if isinstance(price, str):
                price = int(re.sub(r'[^\d]', '', price) or 0)
            
            # Extraer dirección
            address = item.get("address") or ""
            if isinstance(address, dict):
                address = address.get("streetAddress", "")
            
            # Extraer ciudad/estado del item si no se proporcionaron
            item_city = city
            item_state = state
            if not item_city:
                addr_info = item.get("address", {})
                if isinstance(addr_info, dict):
                    item_city = addr_info.get("city", "")
                    item_state = addr_info.get("state", "")
            
            listing = HousingListing(
                id=f"zillow_{zpid}",
                source="zillow",
                address=address,
                city=item_city,
                state=item_state,
                zip_code=item.get("addressZipcode", ""),
                price=price,
                beds=item.get("beds") or 0,
                baths=item.get("baths") or 0,
                sqft=item.get("area") or item.get("livingArea") or 0,
                property_type=item.get("propertyType", "apartment"),
                listing_type="rent" if "rent" in str(item.get("statusText", "")).lower() else "sale",
                photo_url=item.get("imgSrc") or item.get("image") or "",
                detail_url=item.get("detailUrl") or f"https://www.zillow.com/homedetails/{zpid}_zpid/",
                lat=item.get("latLong", {}).get("latitude", 0) if isinstance(item.get("latLong"), dict) else 0,
                lng=item.get("latLong", {}).get("longitude", 0) if isinstance(item.get("latLong"), dict) else 0,
            )
            
            return listing
        except Exception as e:
            logger.error(f"Error parsing Zillow item: {e}")
            return None
    
    def _parse_zillow_html(self, html: str, city: str, state: str) -> List[HousingListing]:
        """Parsea HTML de Zillow directamente"""
        listings = []
        soup = BeautifulSoup(html, "html.parser")
        
        # Buscar cards de propiedades
        property_cards = soup.find_all("article", {"data-test": "property-card"})
        if not property_cards:
            property_cards = soup.find_all("div", class_=re.compile(r"property-card|StyledPropertyCard"))
        
        for card in property_cards[:20]:
            try:
                # Extraer precio
                price_elem = card.find(["span", "div"], class_=re.compile(r"price|Price"))
                price = 0
                if price_elem:
                    price_text = price_elem.get_text()
                    price = int(re.sub(r'[^\d]', '', price_text) or 0)
                
                # Extraer dirección
                address_elem = card.find(["address", "a"], {"data-test": "property-card-addr"})
                if not address_elem:
                    address_elem = card.find(["span", "div"], class_=re.compile(r"address|Address"))
                address = address_elem.get_text().strip() if address_elem else ""
                
                # Extraer beds/baths
                beds = 0
                baths = 0
                details = card.find_all(["span", "li"], class_=re.compile(r"beds|baths|bd|ba"))
                for detail in details:
                    text = detail.get_text().lower()
                    if "bd" in text or "bed" in text:
                        beds = int(re.search(r'\d+', text).group()) if re.search(r'\d+', text) else 0
                    if "ba" in text or "bath" in text:
                        baths = float(re.search(r'[\d.]+', text).group()) if re.search(r'[\d.]+', text) else 0
                
                # Extraer imagen
                img = card.find("img")
                photo_url = img.get("src", "") if img else ""
                
                # Extraer link
                link = card.find("a", href=True)
                detail_url = ""
                if link:
                    href = link.get("href", "")
                    if href.startswith("/"):
                        detail_url = f"https://www.zillow.com{href}"
                    else:
                        detail_url = href
                
                if price > 0 or address:
                    listing = HousingListing(
                        id=f"zillow_html_{random.randint(100000, 999999)}",
                        source="zillow",
                        address=address,
                        city=city,
                        state=state,
                        price=price,
                        beds=beds,
                        baths=baths,
                        photo_url=photo_url,
                        detail_url=detail_url,
                        listing_type="rent",
                    )
                    listings.append(listing)
            except Exception as e:
                logger.error(f"Error parsing Zillow HTML card: {e}")
        
        return listings
    
    async def _scrape_apartments_com(
        self,
        city: str,
        state: str,
        min_price: int = 0,
        max_price: int = 10000,
        beds: int = 0
    ) -> List[HousingListing]:
        """Scrape Apartments.com"""
        listings = []
        
        city_slug = city.lower().replace(" ", "-")
        state_slug = state.lower()
        
        url = f"https://www.apartments.com/{city_slug}-{state_slug}/"
        
        # Agregar filtros
        filters = []
        if min_price > 0:
            filters.append(f"min-{min_price}")
        if max_price < 10000:
            filters.append(f"max-{max_price}")
        if beds > 0:
            filters.append(f"{beds}-bedrooms")
        
        if filters:
            url += "-".join(filters) + "/"
        
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(url, headers=self._get_headers())
                
                if response.status_code != 200:
                    logger.warning(f"Apartments.com returned {response.status_code}")
                    return listings
                
                soup = BeautifulSoup(response.text, "html.parser")
                
                # Buscar placards de propiedades
                placards = soup.find_all("article", class_=re.compile(r"placard|property"))
                if not placards:
                    placards = soup.find_all("li", class_=re.compile(r"placard|mortar-wrapper"))
                
                for placard in placards[:20]:
                    try:
                        # Nombre/Dirección
                        name_elem = placard.find(["span", "div"], class_=re.compile(r"property-title|title"))
                        name = name_elem.get_text().strip() if name_elem else ""
                        
                        address_elem = placard.find(["div", "span"], class_=re.compile(r"property-address|address"))
                        address = address_elem.get_text().strip() if address_elem else name
                        
                        # Precio
                        price_elem = placard.find(["span", "p"], class_=re.compile(r"price|rent"))
                        price = 0
                        if price_elem:
                            price_text = price_elem.get_text()
                            # Buscar rango de precios y tomar el mínimo
                            prices = re.findall(r'\$?([\d,]+)', price_text)
                            if prices:
                                price = int(prices[0].replace(",", ""))
                        
                        # Beds/Baths
                        beds_elem = placard.find(["span", "p"], class_=re.compile(r"bed"))
                        beds_val = 0
                        if beds_elem:
                            beds_match = re.search(r'(\d+)', beds_elem.get_text())
                            beds_val = int(beds_match.group(1)) if beds_match else 0
                        
                        baths_elem = placard.find(["span", "p"], class_=re.compile(r"bath"))
                        baths_val = 0
                        if baths_elem:
                            baths_match = re.search(r'([\d.]+)', baths_elem.get_text())
                            baths_val = float(baths_match.group(1)) if baths_match else 0
                        
                        # Imagen
                        img = placard.find("img")
                        photo_url = ""
                        if img:
                            photo_url = img.get("data-src") or img.get("src") or ""
                        
                        # Link
                        link = placard.find("a", href=True)
                        detail_url = link.get("href", "") if link else ""
                        if detail_url and not detail_url.startswith("http"):
                            detail_url = f"https://www.apartments.com{detail_url}"
                        
                        if price > 0 or address:
                            listing = HousingListing(
                                id=f"apartments_{random.randint(100000, 999999)}",
                                source="apartments.com",
                                address=address,
                                city=city,
                                state=state,
                                price=price,
                                beds=beds_val,
                                baths=baths_val,
                                photo_url=photo_url,
                                detail_url=detail_url,
                                listing_type="rent",
                                property_type="apartment",
                            )
                            listings.append(listing)
                    except Exception as e:
                        logger.error(f"Error parsing Apartments.com placard: {e}")
        
        except Exception as e:
            logger.error(f"Apartments.com scrape exception: {e}")
        
        return listings


# Instancia global
housing_scraper = HousingScraper()


# Funciones helper
async def search_rentals(city: str, state: str, **kwargs) -> List[HousingListing]:
    """Busca rentals"""
    return await housing_scraper.search_rentals(city, state, **kwargs)


def search_rentals_sync(city: str, state: str, **kwargs) -> List[HousingListing]:
    """Versión síncrona para compatibilidad"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(housing_scraper.search_rentals(city, state, **kwargs))
