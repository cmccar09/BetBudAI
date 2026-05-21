"""
Enrichment module - multi-source data enrichment pipeline
Sources: Betfair, Sporting Life, Racing API, OurHub
"""

from .pipeline import (
    enrich_race_data,
    parallel_fetch_enrichment,
    run_full_enrichment_pipeline,
    fetch_todays_races,
)

try:
    from .form_enricher import enrich_runners, get_form_signals, fetch_form, _dist_to_furlongs
except ImportError:
    pass

try:
    from .betfair_fetcher import (
        get_live_betfair_races,
        get_betfair_session,
        fetch_betfair_markets,
        fetch_betfair_odds,
        fetch_betfair_sp,
    )
except ImportError:
    pass

try:
    from .racing_api_client import (
        get_free_racecards,
        get_free_results_today,
        enrich_races_from_racecards,
    )
except ImportError:
    pass

try:
    from .ourhub_enricher import fetch_ourhub_data, enrich_races as ourhub_enrich_races
except ImportError:
    pass

__all__ = [
    'enrich_race_data',
    'parallel_fetch_enrichment',
    'run_full_enrichment_pipeline',
    'fetch_todays_races',
]

