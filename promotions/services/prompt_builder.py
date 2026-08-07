from typing import Dict, Any

class PromptBuilder:
    @staticmethod
    def build_flight_prompt(flight_data: Dict[str, Any]) -> str:
        """
        Takes raw Elasticsearch flight data and formats a strict prompt for the AI.
        """
        f_num = flight_data.get("FlightNum", "Unknown")
        carrier = flight_data.get("Carrier", "Unknown Airlines")
        dep_time = flight_data.get("timestamp", "Unknown time")
        
        origin_city = flight_data.get("OriginCityName", "Unknown City")
        origin_country = flight_data.get("OriginCountry", "Unknown Country")
        origin = f"{origin_city}, {origin_country}"
        
        dest_city = flight_data.get("DestCityName", "Unknown City")
        dest_country = flight_data.get("DestCountry", "Unknown Country")
        dest = f"{dest_city}, {dest_country}"
        
        price = flight_data.get("AvgTicketPrice", 0)
        duration_mins = flight_data.get("FlightTimeMin", 0)
        distance = flight_data.get("DistanceMiles", 0)
        
        return f"""You are a travel marketing copywriter.

Create promotional content for the supplied flight.

Use only the provided flight information.
Do not invent discounts, seat availability, amenities, baggage policies,
booking availability, guarantees, or airline benefits.

Flight details:
- Flight number: {f_num}
- Carrier: {carrier}
- Departure time: {dep_time}
- Origin: {origin}
- Destination: {dest}
- Average ticket price: ${price}
- Flight duration: {duration_mins} minutes
- Distance: {distance} miles

Return valid JSON using exactly this structure:

{{
  "title": "<promotional title>",
  "content": "<promotional content>"
}}"""
