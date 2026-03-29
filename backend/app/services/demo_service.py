import httpx
import random
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Generator
import io
import sys

# We need to target the running backend service
# Since this service runs INSIDE the backend, we should use internal calls where possible,
# but to keep the logic identical to the demo script (which acts as a client), we'll keep using httpx
# pointing to localhost.
BASE_URL = "http://127.0.0.1:8000/api/v1"

class DemoLogger:
    def __init__(self):
        self.logs = []
    
    def log(self, message: str = ""):
        self.logs.append(message)
    
    def get_logs(self) -> List[str]:
        return self.logs

def demo_1_show_stations(logger: DemoLogger):
    """Show all available stations with pricing"""
    logger.log("="*60)
    logger.log("[DEMO 1] Station Discovery")
    logger.log("="*60)
    
    try:
        r = httpx.get(f"{BASE_URL}/stations/")
        stations = r.json()
        
        logger.log(f"\n[OK] Found {len(stations)} charging stations:\n")
        for s in stations[:5]:  # Show first 5
            rate = s['pricing']['effective_rate']
            available = sum(1 for c in s['connectors'] if c['status'] == 'available')
            total = len(s['connectors'])
            logger.log(f"  [+] {s['name']}")
            logger.log(f"      Rate: Rs.{rate:.2f}/kWh | Connectors: {available}/{total} available")
            logger.log("")
    except Exception as e:
        logger.log(f"[ERROR] {str(e)}")


def demo_2_dynamic_pricing(logger: DemoLogger):
    """Show dynamic pricing calculation"""
    logger.log("="*60)
    logger.log("[DEMO 2] Dynamic Pricing Engine")
    logger.log("="*60)
    
    try:
        # Get current strategy
        r = httpx.get(f"{BASE_URL}/pricing/strategy/current")
        strategy = r.json()
        logger.log(f"\n[INFO] Current Pricing Strategy:")
        logger.log(f"   Strategy: {strategy.get('pricing_strategy', 'balanced')}")
        logger.log(f"   Hour: {strategy.get('hour_of_day', 0)}")
        logger.log(f"   Is Peak: {strategy.get('is_peak', False)}")
        logger.log(f"   Grid Status: {strategy.get('grid_status', 'normal')}")
        
        # Calculate dynamic price for different scenarios
        logger.log("\n[CALC] Dynamic Pricing for Different Conditions:\n")
        
        scenarios = [
            {"occupancy": 0.2, "grid_load": 0.3, "hour": 14, "label": "Low Demand (Afternoon)"},
            {"occupancy": 0.5, "grid_load": 0.5, "hour": 9, "label": "Medium Demand (Morning)"},
            {"occupancy": 0.9, "grid_load": 0.8, "hour": 18, "label": "Peak Hour (Evening Rush)"},
        ]
        
        for scenario in scenarios:
            r = httpx.post(f"{BASE_URL}/pricing/dynamic", json={
                "current_occupancy": scenario["occupancy"],
                "grid_load": scenario["grid_load"],
                "hour_of_day": scenario["hour"],
                "day_of_week": 2 # Wednesday
            })
            result = r.json()
            logger.log(f"  [+] {scenario['label']}:")
            logger.log(f"      Occupancy: {scenario['occupancy']*100:.0f}% | Grid: {scenario['grid_load']*100:.0f}%")
            
            # Parse stations list
            stations = result.get('stations', [])
            if stations:
                # Show top 2 stations
                for s_data in stations[:2]:
                    logger.log(f"      - {s_data.get('station_name')}:")
                    logger.log(f"        Base: Rs.{s_data.get('base_rate', 0):.2f} -> Dynamic: Rs.{s_data.get('effective_rate', 0):.2f}/kWh")
                    logger.log(f"        Multiplier: {s_data.get('multiplier', 1.0):.2f}x")
                    logger.log(f"        Reasoning: {s_data.get('reasoning', '')}")
            else:
                logger.log("      No station data returned")
            logger.log("")
    except Exception as e:
        logger.log(f"[ERROR] {str(e)}")


def demo_3_simulate_load(logger: DemoLogger):
    """Simulate multiple EVs requesting charging"""
    logger.log("="*60)
    logger.log("[DEMO 3] Load Simulation (Multiple EVs)")
    logger.log("="*60)
    
    num_evs = 20
    logger.log(f"\n[LOAD] Simulating {num_evs} EVs requesting recommendations...")
    
    start_time = time.time()
    
    def simulate_ev(ev_id):
        try:
            # Random location around Bangalore
            lat = 12.9716 + random.uniform(-0.05, 0.05)
            lon = 77.5946 + random.uniform(-0.05, 0.05)
            soc = random.uniform(10, 50)
            
            r = httpx.post(f"{BASE_URL}/stations/recommend", json={
                "user_location": {"latitude": lat, "longitude": lon},
                "battery_soc": soc,
                "max_distance_km": 20,
                "preferences": {
                    "distance_weight": 0.4,
                    "price_weight": 0.3,
                    "speed_weight": 0.2,
                    "availability_weight": 0.1
                }
            }, timeout=10)
            return r.status_code == 200
        except:
            return False
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(simulate_ev, range(num_evs)))
    
    elapsed = time.time() - start_time
    success = sum(results)
    
    logger.log(f"\n[OK] Results:")
    logger.log(f"   Requests: {num_evs}")
    logger.log(f"   Success Rate: {success}/{num_evs} ({success/num_evs*100:.0f}%)")
    logger.log(f"   Total Time: {elapsed:.2f}s")
    logger.log(f"   Avg Response: {elapsed/num_evs*1000:.0f}ms per request")


def demo_4_reservation_flow(logger: DemoLogger):
    """Demo complete reservation and charging flow"""
    logger.log("="*60)
    logger.log("[DEMO 4] Complete Charging Flow")
    logger.log("="*60)
    
    try:
        # Get a station
        r = httpx.get(f"{BASE_URL}/stations/")
        stations = r.json()
        if not stations:
            logger.log("[ERROR] No stations found")
            return

        station = stations[0]
        
        logger.log(f"\n[1] Selected Station: {station['name']}")
        logger.log(f"    Rate: Rs.{station['pricing']['effective_rate']:.2f}/kWh")
        
        # Create reservation
        logger.log("\n[2] Creating Reservation...")
        r = httpx.post(f"{BASE_URL}/reservations/", json={
            "station_id": station['id'],
            "user_email": "demo@ievc-eco.in"
        })
        
        if r.status_code == 200:
            reservation = r.json()
            logger.log(f"    [OK] Reservation ID: {reservation['id'][:8]}...")
            logger.log(f"    Escrow: Rs.{reservation['escrow_amount']:.2f}")
            
            # Start charging
            logger.log("\n[3] Starting Charging Session...")
            r = httpx.post(f"{BASE_URL}/sessions/start", json={
                "reservation_id": reservation['id']
            })
            
            if r.status_code == 200:
                session = r.json()
                logger.log(f"    [OK] Session Started: {session['id'][:8]}...")
                
                # Simulate charging time
                logger.log("\n    [CHARGING] Simulating 2 seconds...")
                time.sleep(2)
                
                # End session
                logger.log("\n[4] Ending Charging Session...")
                energy = random.uniform(20, 40)
                r = httpx.post(f"{BASE_URL}/sessions/{session['id']}/end", json={
                    "energy_delivered_kwh": energy
                })
                
                if r.status_code == 200:
                    result = r.json()
                    logger.log(f"    [OK] Session Complete!")
                    logger.log(f"    Energy: {result['energy_delivered_kwh']:.2f} kWh")
                    logger.log(f"    Cost: Rs.{result['cost']:.2f}")
                else:
                    logger.log(f"    [ERROR] End Error: {r.text}")
            else:
                logger.log(f"    [ERROR] Start Error: {r.text}")
        else:
            logger.log(f"    [ERROR] Reservation Error: {r.text}")
    except Exception as e:
        logger.log(f"[ERROR] {str(e)}")


def demo_5_grid_dashboard(logger: DemoLogger):
    """Show grid monitoring data"""
    logger.log("="*60)
    logger.log("[DEMO 5] Grid Monitoring Dashboard")
    logger.log("="*60)
    
    try:
        r = httpx.get(f"{BASE_URL}/dashboard/grid/load")
        grid = r.json()
        
        logger.log(f"\n[GRID] Status:")
        logger.log(f"   Current Load: {grid.get('current_load', 0)*100:.1f}%")
        logger.log(f"   Status: {grid.get('status', 'normal').upper()}")
        logger.log(f"   Recommendation: {grid.get('recommendation', '')}")
        
        r = httpx.get(f"{BASE_URL}/dashboard/overview")
        overview = r.json()
        
        logger.log(f"\n[STATS] Platform Overview:")
        logger.log(f"   Stations: {overview.get('stations', {}).get('total', 0)} total ({overview.get('stations', {}).get('active', 0)} active)")
        logger.log(f"   Connectors: {overview.get('connectors', {}).get('available', 0)} available / {overview.get('connectors', {}).get('total', 0)} total")
        logger.log(f"   Utilization: {overview.get('connectors', {}).get('utilization', 0)}%")
        logger.log(f"   24h Revenue: Rs.{overview.get('revenue_24h', 0):.2f}")
        logger.log(f"   24h Energy: {overview.get('energy_24h_kwh', 0):.2f} kWh")
    except Exception as e:
        logger.log(f"[ERROR] {str(e)}")


async def run_demo_scenario(demo_id: str) -> List[str]:
    logger = DemoLogger()
    
    demos = {
        "1": demo_1_show_stations,
        "2": demo_2_dynamic_pricing,
        "3": demo_3_simulate_load,
        "4": demo_4_reservation_flow,
        "5": demo_5_grid_dashboard,
    }
    
    if demo_id in demos:
        # Run synchronous demo function
        demos[demo_id](logger)
    else:
        logger.log(f"[ERROR] Unknown demo ID: {demo_id}")
    
    return logger.get_logs()
