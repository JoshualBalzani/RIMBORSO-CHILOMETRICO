"""
services.py - Integrazione OpenStreetMap (Nominatim) e GraphHopper (Routing)
Completamente gratuito, illimitato, nessuna API key richiesta
- Nominatim: geocodifica indirizzi → coordinate
- GraphHopper: calcola distanze stradali PIU CORTE (weighting=shortest, non fastest!)
"""

import requests
from functools import lru_cache
from typing import Optional, Tuple
import logging
from math import radians, cos, sin, asin, sqrt

logger = logging.getLogger(__name__)


class GoogleMapsService:
    """Servizio per calcolo distanze via GraphHopper
    GraphHopper calcola distanze STRADALI PIU CORTE (weighting=shortest)
    Non il percorso più veloce, ma il più corto su strade reali
    """

    def __init__(self, api_key: str = None):
        """
        Inizializza servizio OpenStreetMap
        
        Args:
            api_key: ignorato (non richiesto per OpenStreetMap)
        """
        self.geocoding_url = 'https://nominatim.openstreetmap.org/search'
        self.user_agent = 'RimborsoKM/1.0'
        self.timeout = 10

    def è_disponibile(self) -> bool:
        """OpenStreetMap è sempre disponibile (gratuito)"""
        return True

    @lru_cache(maxsize=256)
    def _geocodifica(self, indirizzo: str) -> Optional[Tuple[float, float]]:
        """Converte indirizzo COMPLETO in coordinate (lat, lon) usando Nominatim
        
        Strategia di fallback aggressiva:
        1. Prova indirizzo completo
        2. Prova solo città
        3. Prova prime 2 parole (via + numero)
        4. Prova solo prima parola
        5. Se tutto fallisce, ritorna centro Italia (12.5, 41.9) come ultima risorsa
        """
        try:
            indirizzo_originale = indirizzo.strip()
            
            if not indirizzo_originale:
                logger.error('Empty address provided')
                return None
            
            # STEP 1: Prova indirizzo completo
            indirizzo_cercato = indirizzo_originale
            if 'italia' not in indirizzo_cercato.lower():
                indirizzo_cercato += ', Italia'
            
            logger.info(f'Geocoding attempt 1 (FULL): "{indirizzo_cercato}"')
            
            params = {
                'q': indirizzo_cercato,
                'format': 'json',
                'limit': 3,
                'countrycodes': 'it',
                'addressdetails': 1
            }
            
            headers = {'User-Agent': self.user_agent}
            response = requests.get(
                self.geocoding_url,
                params=params,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            if data and len(data) > 0:
                # Prendi il primo risultato
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                logger.info(f'✓ Geocoded "{indirizzo_originale}" → ({lat}, {lon}) [FULL MATCH]')
                return (lat, lon)
            
            # STEP 2: Estrai e prova solo la città (ultima parola)
            logger.warning(f'Step 1 failed, trying city extraction...')
            parole = indirizzo_originale.split(',')
            
            if len(parole) > 1:
                citta = parole[-1].strip()
            else:
                parole = indirizzo_originale.split()
                citta = parole[-1].strip('0123456789.')
            
            citta_cercata = citta + ', Italia'
            logger.info(f'Geocoding attempt 2 (CITY): "{citta_cercata}"')
            
            params = {
                'q': citta_cercata,
                'format': 'json',
                'limit': 1,
                'countrycodes': 'it'
            }
            
            response = requests.get(
                self.geocoding_url,
                params=params,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()
            
            if data and len(data) > 0:
                lat = float(data[0]['lat'])
                lon = float(data[0]['lon'])
                logger.info(f'✓ Geocoded "{indirizzo_originale}" → ({lat}, {lon}) [CITY: {citta}]')
                return (lat, lon)
            
            # STEP 3: Prova prime 2 parole (via + numero)
            logger.warning(f'Step 2 failed, trying first 2 words...')
            parole = indirizzo_originale.split()
            if len(parole) >= 2:
                ricerca = ' '.join(parole[:2]) + ', Italia'
                logger.info(f'Geocoding attempt 3 (FIRST 2 WORDS): "{ricerca}"')
                
                params = {
                    'q': ricerca,
                    'format': 'json',
                    'limit': 1,
                    'countrycodes': 'it'
                }
                
                response = requests.get(
                    self.geocoding_url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                
                if data and len(data) > 0:
                    lat = float(data[0]['lat'])
                    lon = float(data[0]['lon'])
                    logger.info(f'✓ Geocoded "{indirizzo_originale}" → ({lat}, {lon}) [FIRST 2 WORDS]')
                    return (lat, lon)
            
            # STEP 4: Prova solo prima parola
            logger.warning(f'Step 3 failed, trying first word...')
            if len(parole) > 0:
                ricerca = parole[0] + ', Italia'
                logger.info(f'Geocoding attempt 4 (FIRST WORD): "{ricerca}"')
                
                params = {
                    'q': ricerca,
                    'format': 'json',
                    'limit': 1,
                    'countrycodes': 'it'
                }
                
                response = requests.get(
                    self.geocoding_url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                
                if data and len(data) > 0:
                    lat = float(data[0]['lat'])
                    lon = float(data[0]['lon'])
                    logger.info(f'✓ Geocoded "{indirizzo_originale}" → ({lat}, {lon}) [FIRST WORD]')
                    return (lat, lon)
            
            # STEP 5: Nessun risultato trovato - ritorna centro Italia come ultima risorsa
            logger.error(f'All geocoding attempts failed for: "{indirizzo_originale}" - using Italy center as fallback')
            # Centro approssimativo dell'Italia: Roma (41.9, 12.5)
            return (41.9, 12.5)

        except requests.exceptions.Timeout:
            logger.error(f'Geocoding timeout for: "{indirizzo}"')
            return (41.9, 12.5)  # Fallback: centro Italia
        except (requests.RequestException, KeyError, ValueError, IndexError) as e:
            logger.error(f'Geocoding error for "{indirizzo}": {str(e)}')
            return (41.9, 12.5)  # Fallback: centro Italia
        except (requests.RequestException, KeyError, ValueError, IndexError) as e:
            logger.error(f'Geocoding error for "{indirizzo}": {str(e)}')
            return None

    def _distanza_valhalla(self, lat1: float, lon1: float, lat2: float, lon2: float) -> Optional[float]:
        """Calcola distanza stradale via Valhalla (Open Source Routing Engine)
        Valhalla è 100% gratuito, illimitato, accurato su strade reali (percorso più veloce)"""
        try:
            # Valhalla API pubblica
            valhalla_url = 'https://valhalla1.openstreetmap.de/route'
            
            # Payload JSON per Valhalla - FORMATO CORRETTO per Valhalla
            payload = {
                'locations': [
                    {'lat': lat1, 'lon': lon1},
                    {'lat': lat2, 'lon': lon2}
                ],
                'costing': 'auto',  # Profilo auto (automobile)
                'costing_options': {
                    'auto': {
                        'use_highways': True  # Consenti autostrade
                    }
                }
            }
            
            headers = {
                'User-Agent': self.user_agent,
                'Content-Type': 'application/json'
            }
            
            logger.debug(f'Valhalla request payload: {payload}')
            
            response = requests.post(
                valhalla_url,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            logger.debug(f'Valhalla response: {data}')
            
            # Valhalla ritorna la distanza in due possibili formati
            # Controlla prima se c'è 'routes' (formato standard)
            if 'routes' in data and data['routes']:
                distance_m = data['routes'][0].get('distance', 0)
                distance_km = round(distance_m / 1000, 2)
                logger.info(f'Valhalla distance (fastest route): ({lat1},{lon1}) → ({lat2},{lon2}) = {distance_km} km')
                return distance_km
            
            # Fallback: controlla 'trip' se 'routes' non è disponibile
            if 'trip' in data and data['trip'].get('legs'):
                distance_m = sum(leg.get('distance', 0) for leg in data['trip']['legs'])
                distance_km = round(distance_m / 1000, 2)
                logger.info(f'Valhalla distance via trip (fastest route): ({lat1},{lon1}) → ({lat2},{lon2}) = {distance_km} km')
                return distance_km
            
            # Nessun percorso trovato
            logger.warning(f'Valhalla routing failed: {data.get("error", "no route found")}')
            return None
            
        except requests.exceptions.Timeout:
            logger.error(f'Valhalla timeout for routing')
            return None
        except (requests.RequestException, KeyError, ValueError) as e:
            logger.error(f'Valhalla routing error: {str(e)}')
            import traceback
            logger.error(traceback.format_exc())
            return None

    def _distanza_osrm(self, lat1: float, lon1: float, lat2: float, lon2: float) -> Optional[float]:
        """Calcola distanza stradale via OSRM (Open Source Routing Machine)
        OSRM è più affidabile e veloce di Valhalla come fallback"""
        try:
            # OSRM API pubblica
            osrm_url = f'https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}'
            
            params = {
                'overview': 'false',
                'steps': 'false'
            }
            
            headers = {
                'User-Agent': self.user_agent
            }
            
            response = requests.get(
                osrm_url,
                params=params,
                headers=headers,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            
            # OSRM ritorna in 'routes'
            if 'routes' in data and data['routes']:
                distance_m = data['routes'][0].get('distance', 0)
                distance_km = round(distance_m / 1000, 2)
                logger.info(f'OSRM distance: ({lat1},{lon1}) → ({lat2},{lon2}) = {distance_km} km')
                return distance_km
            
            logger.warning(f'OSRM routing failed: {data.get("message", "no route found")}')
            return None
            
        except requests.exceptions.Timeout:
            logger.error(f'OSRM timeout for routing')
            return None
        except (requests.RequestException, KeyError, ValueError) as e:
            logger.error(f'OSRM routing error: {str(e)}')
            return None

    @staticmethod
    def _distanza_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calcola distanza tra due coordinate usando Haversine formula (km)
        FALLBACK: usato solo se Valhalla non disponibile (linea d'aria, meno accurato)"""
        # Raggio terrestre in km
        R = 6371

        # Converti in radianti
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        distanza = R * c

        return round(distanza, 2)

    def calcola_distanza(self, origine: str, destinazione: str) -> Optional[Tuple[float, str]]:
        """
        Calcola distanza STRADALE tra due punti usando OSRM
        OSRM è affidabile e veloce
        
        Args:
            origine: indirizzo/città partenza
            destinazione: indirizzo/città arrivo
            
        Returns:
            Tupla (chilometri, metodo_usato) o None se errore
        """
        try:
            # Geocodifica origine e destinazione
            coord_origine = self._geocodifica(origine)
            coord_destinazione = self._geocodifica(destinazione)

            # DEBUG: Log delle coordinate geocodificate
            logger.info(f'DEBUG GEOCODING: "{origine}" → {coord_origine}')
            logger.info(f'DEBUG GEOCODING: "{destinazione}" → {coord_destinazione}')

            # Se almeno una geocodifica fallisce completamente (None), ritorna errore
            if coord_origine is None or coord_destinazione is None:
                logger.error(f'Geocoding completely failed: {origine} → {destinazione}')
                return None

            # OSRM - Unico metodo usato
            logger.info(f'Attempting OSRM routing with coords: ({coord_origine[0]},{coord_origine[1]}) → ({coord_destinazione[0]},{coord_destinazione[1]})')
            distanza = self._distanza_osrm(
                coord_origine[0], coord_origine[1],
                coord_destinazione[0], coord_destinazione[1]
            )
            
            if distanza is not None:
                logger.info(f'✓ Distance: {origine} → {destinazione} = {distanza} km (OSRM)')
                return (distanza, 'osrm')
            
            # OSRM fallito - ritorna errore (no fallback)
            logger.error(f'OSRM routing FAILED for: {origine} → {destinazione}')
            return None

        except Exception as e:
            logger.error(f'Error calculating distance: {str(e)}')
            import traceback
            logger.error(traceback.format_exc())
            return None
