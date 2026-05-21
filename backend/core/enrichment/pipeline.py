"""
Enrichment pipeline - orchestrates multi-source data fetching
Fetches from: Betfair, Sporting Life, Racing API, OurHub
Merges results into enriched race/horse data
"""

from typing import Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Import real enrichment modules
try:
    from .betfair_fetcher import get_live_betfair_races, get_betfair_session
    BETFAIR_AVAILABLE = True
except ImportError:
    BETFAIR_AVAILABLE = False

try:
    from .form_enricher import enrich_runners, get_form_signals
    FORM_ENRICHER_AVAILABLE = True
except ImportError:
    FORM_ENRICHER_AVAILABLE = False

try:
    from .racing_api_client import enrich_races_from_racecards, get_free_results_today
    RACING_API_AVAILABLE = True
except ImportError:
    RACING_API_AVAILABLE = False

try:
    from .ourhub_enricher import fetch_ourhub_data, enrich_races as ourhub_enrich_races
    OURHUB_AVAILABLE = True
except ImportError:
    OURHUB_AVAILABLE = False

try:
    from ...utils.weather_going_inference import check_all_tracks_going
    WEATHER_AVAILABLE = True
except ImportError:
    try:
        from backend.utils.weather_going_inference import check_all_tracks_going
        WEATHER_AVAILABLE = True
    except ImportError:
        WEATHER_AVAILABLE = False

try:
    from .free_feeds import enrich_races_with_free_signals
    FREE_FEEDS_AVAILABLE = True
except ImportError:
    FREE_FEEDS_AVAILABLE = False


def fetch_todays_races() -> List[Dict[str, Any]]:
    """Fetch today's live horse races from Betfair."""
    if not BETFAIR_AVAILABLE:
        logger.warning("Betfair fetcher not available")
        return []
    try:
        return get_live_betfair_races()
    except Exception as e:
        logger.error(f"Betfair fetch failed: {e}")
        return []


def enrich_race_data(race_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich a single race with multi-source information.
    Called per-race in parallel by parallel_fetch_enrichment.
    """
    enriched = race_data.copy()
    enriched['enrichment_status'] = {
        'betfair': True,   # already populated from Betfair fetch
        'form': False,
        'racing_api': False,
        'ourhub': False,
        'weather': False,
    }
    return enriched


def run_full_enrichment_pipeline(races: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Full enrichment pipeline: form → Racing API → OurHub → weather/going.
    Mutates races in-place and returns them.
    """
    if not races:
        return races

    today = datetime.now().strftime('%Y-%m-%d')

    # Step 1: SL form history (1 request per race racecard)
    if FORM_ENRICHER_AVAILABLE:
        try:
            races = enrich_runners(races, verbose=True)
            logger.info(f"[enrichment] SL form enrichment complete")
        except Exception as e:
            logger.warning(f"[enrichment] Form enrichment failed: {e}")

    # Step 2: Racing API racecard data (going, distance, race class)
    if RACING_API_AVAILABLE:
        try:
            races = enrich_races_from_racecards(races)
            logger.info(f"[enrichment] Racing API enrichment complete")
        except Exception as e:
            logger.warning(f"[enrichment] Racing API enrichment failed: {e}")

    # Step 3: OurHub (trainer/jockey stats, predictions, confirmed going)
    if OURHUB_AVAILABLE:
        try:
            oh_data = fetch_ourhub_data(today)
            races = ourhub_enrich_races(races, oh_data)
            logger.info(f"[enrichment] OurHub enrichment complete")
        except Exception as e:
            logger.warning(f"[enrichment] OurHub enrichment failed: {e}")

    # Step 4: Weather/going inference (fallback when official not declared)
    if WEATHER_AVAILABLE:
        try:
            courses = list({r.get('course', '') for r in races if r.get('course')})
            going_data = check_all_tracks_going(tracks=courses, use_official=True)
            # Inject going into race data
            for race in races:
                course = race.get('course', '')
                if course in going_data and not race.get('going'):
                    race['going'] = going_data[course].get('going', '')
            logger.info(f"[enrichment] Going/weather enrichment complete for {len(going_data)} tracks")
        except Exception as e:
            logger.warning(f"[enrichment] Weather enrichment failed: {e}")

    # Step 5: Free feeds (Open-Meteo + field-relative market context)
    if FREE_FEEDS_AVAILABLE:
        try:
            races = enrich_races_with_free_signals(races)
            logger.info("[enrichment] Free feeds enrichment complete")
        except Exception as e:
            logger.warning(f"[enrichment] Free feeds enrichment failed: {e}")

    return races


def parallel_fetch_enrichment(races: List[Dict[str, Any]], max_workers: int = 5) -> List[Dict[str, Any]]:
    """
    Fetch enrichment data for multiple races in parallel.
    NOTE: Most enrichment is batch-based (one call per venue).
    Use run_full_enrichment_pipeline() for the main pipeline.
    """
    enriched_races = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(enrich_race_data, race): race for race in races}

        for future in as_completed(futures):
            try:
                enriched = future.result(timeout=30)
                enriched_races.append(enriched)
            except Exception as e:
                race = futures[future]
                logger.warning(f"Enrichment failed for race {race.get('race_id')}: {e}")
                enriched_races.append(race)

    return enriched_races

