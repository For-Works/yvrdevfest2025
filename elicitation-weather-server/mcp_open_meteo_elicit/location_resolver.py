"""
Location resolution and disambiguation logic.

This module handles resolving location names to coordinates, including
managing ambiguous location results through MCP elicitation when multiple
locations are found for a given search term.

MCP specification: https://modelcontextprotocol.io/specification/draft/client/elicitation
SDK documentation: https://github.com/modelcontextprotocol/python-sdk?tab=readme-ov-file#elicitation
"""

from mcp.server.fastmcp import Context # 
from .models import LocationInfo, LocationChoice
from .api_client import search_locations
from .config import MAX_LOCATION_ELICITATION_OPTIONS


async def resolve_location(location_name: str, ctx: Context) -> LocationInfo:
    """
    Resolve a location name to coordinates, handling ambiguous results with elicitation
    """
    await ctx.info(f"resolve_location called with location_name='{location_name}'")
    
    try:
        await ctx.debug(f"Searching for locations matching '{location_name}'")
        locations = await search_locations(location_name, limit=10)
        await ctx.info(f"Location search returned {len(locations)} results")
        
        if not locations:
            await ctx.error(f"No locations found for '{location_name}'")
            raise ValueError(f"No locations found for '{location_name}'. Please try a different search term.")
        
        if len(locations) == 1:
            # Single result, use it directly
            await ctx.info(f"Single location found: {locations[0]['name']}, {locations[0].get('country', '')}")
            loc = locations[0]
            return LocationInfo(
                id=loc["id"],
                name=loc["name"],
                latitude=loc["latitude"],
                longitude=loc["longitude"],
                country=loc.get("country", ""),
                admin1=loc.get("admin1"),
                admin2=loc.get("admin2"),
                timezone=loc["timezone"],
                population=loc.get("population"),
                elevation=loc.get("elevation")
            )
        
        # Multiple results - use elicitation to let user choose
        await ctx.warning(f"Multiple locations found ({len(locations)}), initiating user elicitation")
        location_options = []
        options_count = min(len(locations), MAX_LOCATION_ELICITATION_OPTIONS)
        await ctx.debug(f"Preparing {options_count} location options for elicitation")
        
        for i, loc in enumerate(locations[:MAX_LOCATION_ELICITATION_OPTIONS]):  # Limit to top 5 for usability
            admin_parts = []
            if loc.get("admin1"):
                admin_parts.append(loc["admin1"])
            if loc.get("admin2") and loc.get("admin2") != loc.get("admin1"):
                admin_parts.append(loc["admin2"])
            
            admin_str = f", {', '.join(admin_parts)}" if admin_parts else ""
            pop_str = f" (pop. {loc['population']:,})" if loc.get("population") else ""
            
            option_text = f"{i+1}. {loc['name']}{admin_str}, {loc['country']}{pop_str}"
            location_options.append(option_text)
            await ctx.debug(f"Option {i+1}: {loc['name']}, {loc.get('country', '')}")
        
        options_text = "\n".join(location_options)
        
        # Create elicitation message
        message = f"Multiple locations found for '{location_name}':\n\n{options_text}\n\nPlease select the correct location:"
        
        # Use elicitation to get user choice
        await ctx.info("Sending elicitation request to user")
        result = await ctx.elicit(
            message=message,
            schema=LocationChoice
        )
        
        if result.action != "accept" or not result.data:
            await ctx.error("Location selection was cancelled or invalid")
            raise ValueError("Location selection was cancelled or invalid.")
        
        selected_index = result.data.selected_location_id - 1
        await ctx.debug(f"User selected option {result.data.selected_location_id} (index {selected_index})")
        
        if selected_index < 0 or selected_index >= len(locations[:MAX_LOCATION_ELICITATION_OPTIONS]):
            await ctx.error(f"Invalid location selection: {result.data.selected_location_id}")
            raise ValueError("Invalid location selection. Please choose a number from the list.")
        
        selected_location = locations[selected_index]
        await ctx.info(f"Location resolved to: {selected_location['name']}, {selected_location.get('country', '')}")
        
        return LocationInfo(
            id=selected_location["id"],
            name=selected_location["name"],
            latitude=selected_location["latitude"],
            longitude=selected_location["longitude"],
            country=selected_location.get("country", ""),
            admin1=selected_location.get("admin1"),
            admin2=selected_location.get("admin2"),
            timezone=selected_location["timezone"],
            population=selected_location.get("population"),
            elevation=selected_location.get("elevation")
        )
        
    except Exception as e:
        await ctx.error(f"Error in resolve_location: {str(e)}")
        raise
