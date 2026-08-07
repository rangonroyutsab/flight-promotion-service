import logging

from elasticsearch import Elasticsearch
from django.conf import settings
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import elasticsearch.exceptions

logger = logging.getLogger(__name__)


class ElasticsearchClient:
    def __init__(self):
        # NOTE: xpack.security.enabled=false is set in docker-compose.yml,
        # so auth is effectively a no-op. Kept for forward compatibility if
        # security is later enabled.
        self.client = Elasticsearch(
            settings.ELASTICSEARCH_URL,
            basic_auth=(settings.ELASTICSEARCH_USERNAME, settings.ELASTICSEARCH_PASSWORD)
        )
        self.index = settings.ELASTICSEARCH_INDEX

    @retry(
        stop=stop_after_attempt(settings.DEFAULT_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((elasticsearch.exceptions.ConnectionError, elasticsearch.exceptions.ApiError))
    )
    def search_flights(self, start_utc: str, end_utc: str):
        """
        Query Elasticsearch for eligible flights based on PLAN.md Section 11.
        """
        query = {
            "size": 5,
            "track_total_hits": False,
            "_source": [
                "timestamp", "FlightNum", "Carrier", "Origin", "OriginAirportID",
                "OriginCityName", "OriginCountry", "OriginRegion", "OriginWeather",
                "OriginLocation", "Dest", "DestAirportID", "DestCityName",
                "DestCountry", "DestRegion", "DestWeather", "DestLocation",
                "AvgTicketPrice", "FlightTimeHour", "FlightTimeMin", "DistanceMiles",
                "DistanceKilometers", "dayOfWeek", "FlightDelay", "FlightDelayMin",
                "FlightDelayType", "Cancelled"
            ],
            "query": {
                "bool": {
                    "filter": [
                        {
                            "range": {
                                "timestamp": {
                                    "gte": start_utc,
                                    "lt": end_utc
                                }
                            }
                        },
                        {"term": {"DestCountry": "US"}},
                        {"term": {"FlightDelay": False}},
                        {"term": {"FlightDelayMin": 0}},
                        {"term": {"Cancelled": False}},
                        {"range": {"AvgTicketPrice": {"gt": 500}}}
                    ]
                }
            },
            "sort": [
                {"timestamp": {"order": "asc"}},
                {"AvgTicketPrice": {"order": "desc"}},
                {"FlightNum": {"order": "asc"}}
            ]
        }

        response = self.client.search(index=self.index, body=query)
        return response.get('hits', {}).get('hits', [])
