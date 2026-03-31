import httpx
import random
import asyncio
import time
from typing import List, Dict, Any

# Target the running backend service.
BASE_URL = "http://127.0.0.1:8000/api/v1"

class DemoLogger:
    def __init__(self):
        self.logs = []
    
    def log(self, message: str = ""):
        self.logs.append(message)
    
    def get_logs(self) -> List[str]:
        return self.logs

async def demo_1_show_stations(logger: DemoLogger, client: httpx.AsyncClient):
    """Show all available stations with pricing"""
    logger.log("="*60)
    logger.log("[DEMO 1] Station Discovery")
    logger.log("="*60)
    
    try:
        r = await client.get(f"{BASE_URL}/stations/")
        stations = r.json()
        
        logger.log(f"\n[OK] Found {len(stations)} charging stations:\n")
        for s in stations[:5]:
            rate = s['pricing']['effective_rate']
            available = sum(1 for c in s['connectors'] if c['status'] == 'available')
            total = len(s['connectors'])
            logger.log(f"  [+] {s['name']}")
            logger.log(f"      Rate: Rs.{rate:.2f}/kWh | Connectors: {available}/{total} available")
            logger.log("")
    except Exception as e:
        logger.log(f"[ERROR] {str(e)}")

async def demo_2_dynamic_pricing(logger: DemoLogger, client: httpx.AsyncClient):
    """Show dynamic pricing calculation"""
    logger.log("="*60)
    logger.log("[DEMO 2] Dynamic Pricing Engine")
    logger.log("="*60)
    
    try:
        r = await client.get(f"{BASE_URL}/pricing/strategy/current")
        strategy = r.json()
        logger.log(f"\n[INFO] Current Pricing Strategy:")
        logger.log(f"   Strategy: {strategy.get('pricing_strategy', 'balanced')}")
        logger.log(f"   Hour: {strategy.get('hour_of_day', 0)}")
        logger.log(f"   Is Peak: {strategy.get('is_peak', False)}")
        logger.log(f"   Grid Status: {strategy.get('grid_status', 'normal')}")
        
        logger.log("\n[CALC] Dynamic Pricing for Different Conditions:\n")
        
        scenarios = [
            {"occupancy": 0.2, "grid_load": 0.3, "hour": 14, "label": "Low Demand (Afternoon)"},
            {"occupancy": 0.5, "grid_load": 0.5, "hour": 9, "label": "Medium Demand (Morning)"},
            {"occupancy": 0.9, "grid_load": 0.8, "hour": 18, "label": "Peak Hour (Evening Rush)"},
        ]
        
        for scenario in scenarios:
            r = await client.post(f"{BASE_URL}/pricing/dynamic", json={
                "current_occupancy": scenario["occupancy"],
                "grid_load": scenario["grid_load"],
                "hour_of_day": scenario["hour"],
                "day_of_week": 2 # Wednesday
            })
            result = r.json()
            logger.log(f"  [+] {scenario['label']}:")
            logger.log(f"      Occupancy: {scenario['occupancy']*100:.0f}% | Grid: {scenario['grid_load']*100:.0f}%")
            
            stations = result.get('stations', [])
            if stations:
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

async def demo_3_simulate_load(logger: DemoLogger, client: httpx.AsyncClient):
    """Simulate multiple EVs requesting charging"""
    logger.log("="*60)
    logger.log("[DEMO 3] Load Simulation (Multiple EVs)")
    logger.log("="*60)
    
    num_evs = 20
    logger.log(f"\n[LOAD] Simulating {num_evs} concurrent EV driver requests...")
    
    start_time = time.time()
    success_count = 0
    
    # We process in batches to avoid overwhelming the single-worker backend
    # and to provide "live" progress updates if the frontend could stream them.
    # Since we return all logs at once, we'll still gather but with a smaller limit.
    
    async def simulate_ev(i):
        try:
            lat = 12.9716 + random.uniform(-0.05, 0.05)
            lon = 77.5946 + random.uniform(-0.05, 0.05)
            soc = random.uniform(10, 50)
            
            r = await client.post(f"{BASE_URL}/stations/recommend", json={
                "user_location": {"latitude": lat, "longitude": lon},
                "battery_soc": soc,
                "max_distance_km": 20,
                "preferences": {
                    "distance_weight": 0.4,
                    "price_weight": 0.3,
                    "speed_weight": 0.2,
                    "availability_weight": 0.1
                }
            }, timeout=15)
            
            if r.status_code == 200:
                return True
            return False
        except Exception:
            return False

    # Execute in small chunks to show progress capability and maintain server stability
    chunk_size = 5
    all_results = []
    for i in range(0, num_evs, chunk_size):
        logger.log(f"   - Processing batch {i//chunk_size + 1}/{num_evs//chunk_size}...")
        batch_tasks = [simulate_ev(j) for j in range(i, min(i + chunk_size, num_evs))]
        batch_results = await asyncio.gather(*batch_tasks)
        all_results.extend(batch_results)
        # Small artificial delay to allow log observation if streaming were enabled
        await asyncio.sleep(0.1)
    
    elapsed = time.time() - start_time
    success = sum(all_results)
    
    logger.log(f"\n[OK] Aggregated Results:")
    logger.log(f"   Total Requests: {num_evs}")
    logger.log(f"   Success Rate:   {success}/{num_evs} ({success/num_evs*100:.0f}%)")
    logger.log(f"   Total Time:     {elapsed:.2f}s")
    logger.log(f"   Response Avg:   {elapsed/num_evs*1000:.0f}ms")
    logger.log(f"\nNote: In a single-threaded dev environment, 20 concurrent")
    logger.log(f"MCDM requests are processed sequentially by the threadpool.")

async def demo_4_reservation_flow(logger: DemoLogger, client: httpx.AsyncClient):
    """Demo complete reservation and charging flow"""
    logger.log("="*60)
    logger.log("[DEMO 4] Complete Charging Flow")
    logger.log("="*60)
    
    try:
        r = await client.get(f"{BASE_URL}/stations/")
        stations = r.json()
        if not stations:
            logger.log("[ERROR] No stations found")
            return

        station = stations[0]
        logger.log(f"\n[1] Selected Station: {station['name']}")
        
        logger.log("\n[2] Creating Reservation...")
        r = await client.post(f"{BASE_URL}/reservations/", json={
            "station_id": station['id'],
            "user_email": "demo@ievc-eco.in"
        })
        
        if r.status_code == 200:
            res = r.json()
            logger.log(f"    [OK] Reservation ID: {res['id'][:8]}...")
            logger.log(f"    Escrow Locked: Rs.{res['escrow_amount']:.2f}")
            
            logger.log("\n[3] Starting Charging Session...")
            r = await client.post(f"{BASE_URL}/sessions/start", json={"reservation_id": res['id']})
            
            if r.status_code == 200:
                session = r.json()
                logger.log(f"    [OK] Session Active: {session['id'][:8]}...")
                logger.log("    [CHARGING] Transferring energy...")
                await asyncio.sleep(1.5)
                
                logger.log("\n[4] Ending Charging Session...")
                energy = random.uniform(20, 35)
                r = await client.post(f"{BASE_URL}/sessions/{session['id']}/end", json={
                    "energy_delivered_kwh": energy
                })
                
                if r.status_code == 200:
                    fin = r.json()
                    logger.log(f"    [OK] Session Complete!")
                    logger.log(f"    Energy: {fin['energy_delivered_kwh']:.2f} kWh")
                    logger.log(f"    Total Cost: Rs.{fin['cost']:.2f}")
                else:
                    logger.log(f"    [ERROR] End Session Failed")
            else:
                logger.log(f"    [ERROR] Start Session Failed")
        else:
            logger.log(f"    [ERROR] Reservation Failed")
    except Exception as e:
        logger.log(f"[ERROR] {str(e)}")

async def demo_5_grid_dashboard(logger: DemoLogger, client: httpx.AsyncClient):
    """Show grid monitoring data"""
    logger.log("="*60)
    logger.log("[DEMO 5] Grid Monitoring Dashboard")
    logger.log("="*60)
    
    try:
        r = await client.get(f"{BASE_URL}/dashboard/grid/load")
        grid = r.json()
        logger.log(f"\n[GRID] Current Stress: {grid.get('current_load', 0)*100:.1f}%")
        logger.log(f"   Status: {grid.get('status', 'normal').upper()}")
        
        r = await client.get(f"{BASE_URL}/dashboard/overview")
        ov = r.json()
        logger.log(f"\n[STATS] System Metrics:")
        logger.log(f"   Active Stations: {ov['stations']['active']}")
        logger.log(f"   Total Energy (24h): {ov['energy_24h_kwh']:.1f} kWh")
        logger.log(f"   Platform Revenue: Rs.{ov['revenue_24h']:.2f}")
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
        async with httpx.AsyncClient() as client:
            await demos[demo_id](logger, client)
    else:
        logger.log(f"[ERROR] Unknown demo ID: {demo_id}")
    return logger.get_logs()
