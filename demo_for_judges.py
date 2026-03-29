"""
IEVC-eco Demo Scripts for Judges
=================================
Run these to demonstrate different features of the system.

Usage:
  python demo_for_judges.py        # Run all demos
  python demo_for_judges.py 1      # Run specific demo (1-6)
"""
import httpx
import random
import time
import sys
from concurrent.futures import ThreadPoolExecutor

# Set UTF-8 encoding for Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000/api/v1"


def demo_1_show_stations():
    """Show all available stations with pricing"""
    print("\n" + "="*60)
    print("[DEMO 1] Station Discovery")
    print("="*60)
    
    r = httpx.get(f"{BASE_URL}/stations/")
    stations = r.json()
    
    print(f"\n[OK] Found {len(stations)} charging stations:\n")
    for s in stations[:5]:  # Show first 5
        rate = s['pricing']['effective_rate']
        available = sum(1 for c in s['connectors'] if c['status'] == 'available')
        total = len(s['connectors'])
        print(f"  [+] {s['name']}")
        print(f"      Rate: Rs.{rate:.2f}/kWh | Connectors: {available}/{total} available")
        print()


def demo_2_dynamic_pricing():
    """Show dynamic pricing calculation"""
    print("\n" + "="*60)
    print("[DEMO 2] Dynamic Pricing Engine")
    print("="*60)
    
    # Get current strategy
    r = httpx.get(f"{BASE_URL}/pricing/strategy/current")
    strategy = r.json()
    print(f"\n[INFO] Current Pricing Strategy:")
    print(f"   Strategy: {strategy.get('pricing_strategy', 'balanced')}")
    print(f"   Hour: {strategy.get('hour_of_day', 0)}")
    print(f"   Is Peak: {strategy.get('is_peak', False)}")
    print(f"   Grid Status: {strategy.get('grid_status', 'normal')}")
    
    # Calculate dynamic price for different scenarios
    print("\n[CALC] Dynamic Pricing for Different Conditions:\n")
    
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
        print(f"  [+] {scenario['label']}:")
        print(f"      Occupancy: {scenario['occupancy']*100:.0f}% | Grid: {scenario['grid_load']*100:.0f}%")
        
        # Parse stations list
        stations = result.get('stations', [])
        if stations:
            # Show top 2 stations
            for s_data in stations[:2]:
                print(f"      - {s_data.get('station_name')}:")
                print(f"        Base: Rs.{s_data.get('base_rate', 0):.2f} -> Dynamic: Rs.{s_data.get('effective_rate', 0):.2f}/kWh")
                print(f"        Multiplier: {s_data.get('multiplier', 1.0):.2f}x")
                print(f"        Reasoning: {s_data.get('reasoning', '')}")
        else:
            print("      No station data returned")
        print()


def demo_3_simulate_load():
    """Simulate multiple EVs requesting charging"""
    print("\n" + "="*60)
    print("[DEMO 3] Load Simulation (Multiple EVs)")
    print("="*60)
    
    num_evs = 20
    print(f"\n[LOAD] Simulating {num_evs} EVs requesting recommendations...")
    
    start_time = time.time()
    
    def simulate_ev(ev_id):
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
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(simulate_ev, range(num_evs)))
    
    elapsed = time.time() - start_time
    success = sum(results)
    
    print(f"\n[OK] Results:")
    print(f"   Requests: {num_evs}")
    print(f"   Success Rate: {success}/{num_evs} ({success/num_evs*100:.0f}%)")
    print(f"   Total Time: {elapsed:.2f}s")
    print(f"   Avg Response: {elapsed/num_evs*1000:.0f}ms per request")


def demo_4_reservation_flow():
    """Demo complete reservation and charging flow"""
    print("\n" + "="*60)
    print("[DEMO 4] Complete Charging Flow")
    print("="*60)
    
    # Get a station
    r = httpx.get(f"{BASE_URL}/stations/")
    stations = r.json()
    station = stations[0]
    
    print(f"\n[1] Selected Station: {station['name']}")
    print(f"    Rate: Rs.{station['pricing']['effective_rate']:.2f}/kWh")
    
    # Create reservation
    print("\n[2] Creating Reservation...")
    r = httpx.post(f"{BASE_URL}/reservations/", json={
        "station_id": station['id'],
        "user_email": "demo@ievc-eco.in"
    })
    
    if r.status_code == 200:
        reservation = r.json()
        print(f"    [OK] Reservation ID: {reservation['id'][:8]}...")
        print(f"    Escrow: Rs.{reservation['escrow_amount']:.2f}")
        
        # Start charging
        print("\n[3] Starting Charging Session...")
        r = httpx.post(f"{BASE_URL}/sessions/start", json={
            "reservation_id": reservation['id']
        })
        
        if r.status_code == 200:
            session = r.json()
            print(f"    [OK] Session Started: {session['id'][:8]}...")
            
            # Simulate charging time
            print("\n    [CHARGING] Simulating 2 seconds...")
            time.sleep(2)
            
            # End session
            print("\n[4] Ending Charging Session...")
            energy = random.uniform(20, 40)
            r = httpx.post(f"{BASE_URL}/sessions/{session['id']}/end", json={
                "energy_delivered_kwh": energy
            })
            
            if r.status_code == 200:
                result = r.json()
                print(f"    [OK] Session Complete!")
                print(f"    Energy: {result['energy_delivered_kwh']:.2f} kWh")
                print(f"    Cost: Rs.{result['cost']:.2f}")
            else:
                print(f"    [ERROR] End Error: {r.text}")
        else:
            print(f"    [ERROR] Start Error: {r.text}")
    else:
        print(f"    [ERROR] Reservation Error: {r.text}")


def demo_5_grid_dashboard():
    """Show grid monitoring data"""
    print("\n" + "="*60)
    print("[DEMO 5] Grid Monitoring Dashboard")
    print("="*60)
    
    r = httpx.get(f"{BASE_URL}/dashboard/grid/load")
    grid = r.json()
    
    print(f"\n[GRID] Status:")
    print(f"   Current Load: {grid.get('current_load', 0)*100:.1f}%")
    print(f"   Status: {grid.get('status', 'normal').upper()}")
    print(f"   Recommendation: {grid.get('recommendation', '')}")
    
    r = httpx.get(f"{BASE_URL}/dashboard/overview")
    overview = r.json()
    
    print(f"\n[STATS] Platform Overview:")
    print(f"   Stations: {overview.get('stations', {}).get('total', 0)} total ({overview.get('stations', {}).get('active', 0)} active)")
    print(f"   Connectors: {overview.get('connectors', {}).get('available', 0)} available / {overview.get('connectors', {}).get('total', 0)} total")
    print(f"   Utilization: {overview.get('connectors', {}).get('utilization', 0)}%")
    print(f"   24h Revenue: Rs.{overview.get('revenue_24h', 0):.2f}")
    print(f"   24h Energy: {overview.get('energy_24h_kwh', 0):.2f} kWh")


def demo_6_stress_test_info():
    """Info about running stress test"""
    print("\n" + "="*60)
    print("[DEMO 6] MARL Stress Test (1000+ EVs)")
    print("="*60)
    print("""
To run the full MARL stress test with 1000+ EVs:

  cd simulation
  python stress_test.py --num-evs 1000 --duration 60

This will:
  [+] Simulate 1000 EVs requesting charging
  [+] Show real-time metrics and pricing updates
  [+] Demonstrate multi-agent coordination
  [+] Generate performance report

For training the MARL agents:
  python train.py --episodes 100

""")


def run_all_demos():
    """Run all demos in sequence"""
    print("\n" + "="*60)
    print("   IEVC-eco: Intelligent EV Charging Ecosystem")
    print("   Demo Presentation for Judges")
    print("="*60)
    
    demos = [
        ("Station Discovery", demo_1_show_stations),
        ("Dynamic Pricing", demo_2_dynamic_pricing),
        ("Load Simulation", demo_3_simulate_load),
        ("Reservation Flow", demo_4_reservation_flow),
        ("Grid Dashboard", demo_5_grid_dashboard),
        ("Stress Test Info", demo_6_stress_test_info),
    ]
    
    for name, demo in demos:
        try:
            demo()
        except Exception as e:
            print(f"\n[ERROR] {name}: {e}")
        
        input("\n>>> Press Enter for next demo...")
    
    print("\n" + "="*60)
    print("[DONE] Demo Complete! Thank you for watching.")
    print("="*60)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        demo_num = sys.argv[1]
        demos = {
            "1": demo_1_show_stations,
            "2": demo_2_dynamic_pricing,
            "3": demo_3_simulate_load,
            "4": demo_4_reservation_flow,
            "5": demo_5_grid_dashboard,
            "6": demo_6_stress_test_info,
            "all": run_all_demos,
        }
        if demo_num in demos:
            demos[demo_num]()
        else:
            print("Usage: python demo_for_judges.py [1-6|all]")
            print("\nDemos:")
            print("  1 - Station Discovery")
            print("  2 - Dynamic Pricing")
            print("  3 - Load Simulation")
            print("  4 - Reservation Flow")
            print("  5 - Grid Dashboard")
            print("  6 - Stress Test Info")
            print("  all - Run all demos")
    else:
        run_all_demos()
