"""
API client for interacting with Open-Meteo services.

This module handles all HTTP communication with the Open-Meteo geocoding
and weather forecast APIs, including error handling and response parsing.
"""

import httpx
import logging
from typing import List, Dict, Any, Optional
from .config import GEOCODING_API_URL, WEATHER_API_URL, MAX_LOCATION_SEARCH_RESULTS

# Set up basic logging for the API client
logger = logging.getLogger(__name__)


async def search_locations(location_name: str, limit: int = 10) -> List[Dict[str, Any]]:
    """Search for locations using the geocoding API"""
    logger.info(f"Searching for locations: '{location_name}' with limit {limit}")
    
    params = {
        "name": location_name,
        "count": min(limit, MAX_LOCATION_SEARCH_RESULTS),
        "format": "json"
    }
    
    # Configure httpx client with more robust settings
    timeout = httpx.Timeout(30.0, connect=10.0)  # 30s total, 10s connect
    headers = {
        "User-Agent": "MCP-Weather-Server/1.0",
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate"
    }
    
    try:
        async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True) as client:
            logger.debug(f"Making geocoding API request with params: {params}")
            logger.debug(f"Request URL: {GEOCODING_API_URL}")
            
            response = await client.get(GEOCODING_API_URL, params=params)
            logger.debug(f"search_locations GET URI: {response.request.url}")
            logger.debug(f"Response status: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                logger.info(f"Geocoding API returned {len(results)} results")
                return results
            else:
                logger.error(f"Geocoding API error: HTTP {response.status_code}")
                logger.error(f"Response content: {response.text}")
                try:
                    error_data = response.json()
                    error_msg = error_data.get('reason', 'Unknown error')
                except:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                raise ValueError(f"Geocoding API error: {error_msg}")
                
    except httpx.TimeoutException as e:
        logger.error(f"Timeout error during geocoding request: {str(e)}")
        raise ValueError(f"Request timeout - the geocoding service may be temporarily unavailable: {str(e)}")
    except httpx.ConnectError as e:
        logger.error(f"Connection error during geocoding request: {str(e)}")
        raise ValueError(f"Failed to connect to geocoding service. Please check your internet connection: {str(e)}")
    except httpx.RequestError as e:
        logger.error(f"Network error during geocoding request: {str(e)}")
        raise ValueError(f"Network error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in search_locations: {str(e)}")
        raise


async def get_weather_data(latitude: float, longitude: float, 
                          current: Optional[List[str]] = None,
                          hourly: Optional[List[str]] = None,
                          daily: Optional[List[str]] = None,
                          forecast_days: int = 7,
                          temperature_unit: str = "celsius",
                          wind_speed_unit: str = "kmh",
                          precipitation_unit: str = "mm") -> Dict[str, Any]:
    """Get weather data from Open-Meteo forecast API"""
    logger.info(f"Getting weather data for coordinates: {latitude}, {longitude}")
    
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "temperature_unit": temperature_unit,
        "wind_speed_unit": wind_speed_unit,
        "precipitation_unit": precipitation_unit,
        "forecast_days": forecast_days
    }
    
    if current:
        params["current"] = ",".join(current)
        logger.debug(f"Current parameters: {current}")
    if hourly:
        params["hourly"] = ",".join(hourly)
        logger.debug(f"Hourly parameters: {hourly}")
    if daily:
        params["daily"] = ",".join(daily)
        logger.debug(f"Daily parameters: {daily}")
    
    # Configure httpx client with more robust settings
    timeout = httpx.Timeout(30.0, connect=10.0)  # 30s total, 10s connect
    headers = {
        "User-Agent": "MCP-Weather-Server/1.0",
        "Accept": "application/json",
        "Accept-Encoding": "gzip, deflate"
    }
    
    try:
        async with httpx.AsyncClient(timeout=timeout, headers=headers, follow_redirects=True) as client:
            logger.debug(f"Making weather API request with params: {params}")
            logger.debug(f"Request URL: {WEATHER_API_URL}")
            
            response = await client.get(WEATHER_API_URL, params=params)
            logger.debug(f"Weather API GET URI: {response.request.url}")
            logger.debug(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                logger.info("Weather API request successful")
                logger.debug(f"Weather data keys: {list(data.keys())}")
                return data
            else:
                logger.error(f"Weather API error: HTTP {response.status_code}")
                logger.error(f"Response content: {response.text}")
                try:
                    error_data = response.json()
                    error_msg = error_data.get('reason', 'Unknown error')
                except:
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                raise ValueError(f"Weather API error: {error_msg}")
                
    except httpx.TimeoutException as e:
        logger.error(f"Timeout error during weather request: {str(e)}")
        raise ValueError(f"Request timeout - the weather service may be temporarily unavailable: {str(e)}")
    except httpx.ConnectError as e:
        logger.error(f"Connection error during weather request: {str(e)}")
        raise ValueError(f"Failed to connect to weather service. Please check your internet connection: {str(e)}")
    except httpx.RequestError as e:
        logger.error(f"Network error during weather request: {str(e)}")
        raise ValueError(f"Network error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in get_weather_data: {str(e)}")
        raise
