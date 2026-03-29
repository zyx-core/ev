"""
Stress Test Script
Simulate 1,000+ EVs to stress test the IEVC-eco system
"""
import argparse
import numpy as np
import matplotlib.pyplot as plt
from typing import Dict, List
import time
import json
from datetime import datetime
import sys
import os

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env.charging_env import ChargingEnvironment


class StressTest:
    """
    Stress test for IEVC-eco system
    
    Simulates large numbers of EVs to test:
    - System scalability
    - Grid load handling
    - Price stability
    - Agent coordination
    """
    
    def __init__(
        self,
        num_evs: int = 1000,
        num_stations: int = 50,
        num_cpos: int = 10,
        max_steps: int = 576,  # 48 hours
        seed: int = 42
    ):
        """
        Initialize stress test
        
        Args:
            num_evs: Number of EV agents to simulate
            num_stations: Number of charging stations
            num_cpos: Number of CPO agents
            max_steps: Maximum simulation steps
            seed: Random seed
        """
        np.random.seed(seed)
        
        self.num_evs = num_evs
        self.num_stations = num_stations
        self.num_cpos = num_cpos
        self.max_steps = max_steps
        
        # Metrics
        self.step_times: List[float] = []
        self.grid_loads: List[float] = []
        self.avg_prices: List[float] = []
        self.total_revenue: List[float] = []
        self.station_utilization: List[np.ndarray] = []
        self.wait_times: List[float] = []
        
        print(f"\n{'='*60}")
        print("IEVC-eco Stress Test Configuration")
        print(f"{'='*60}")
        print(f"EVs:       {num_evs:,}")
        print(f"Stations:  {num_stations}")
        print(f"CPOs:      {num_cpos}")
        print(f"Duration:  {max_steps} steps ({max_steps * 5 / 60:.1f} hours)")
        print(f"{'='*60}\n")
    
    def run(self, verbose: bool = True) -> Dict:
        """
        Run stress test
        
        Returns:
            Test results and metrics
        """
        print("Initializing environment...", end=" ", flush=True)
        start_init = time.time()
        
        env = ChargingEnvironment(
            num_evs=self.num_evs,
            num_stations=self.num_stations,
            num_cpos=self.num_cpos,
            max_steps=self.max_steps
        )
        
        init_time = time.time() - start_init
        print(f"Done ({init_time:.2f}s)")
        
        print("Starting simulation...\n")
        
        observations, _ = env.reset(seed=42)
        
        total_start = time.time()
        step = 0
        cumulative_revenue = 0.0
        
        while env.agents and step < self.max_steps:
            step_start = time.time()
            
            # Generate random actions for all agents
            actions = {}
            for agent_id in env.agents:
                actions[agent_id] = env.action_space(agent_id).sample()
            
            # Step environment
            observations, rewards, terminated, truncated, infos = env.step(actions)
            
            step_time = time.time() - step_start
            self.step_times.append(step_time)
            
            # Collect metrics
            self.grid_loads.append(env.grid_load)
            self.avg_prices.append(np.mean(env.station_prices))
            
            # Calculate revenue
            cpo_rewards = sum(
                rewards.get(f"cpo_{i}", 0) for i in range(self.num_cpos)
            )
            cumulative_revenue += cpo_rewards
            self.total_revenue.append(cumulative_revenue)
            
            # Station utilization
            utilization = env.station_occupancy / env.station_capacities
            self.station_utilization.append(utilization.copy())
            
            # Estimate wait times based on occupancy
            avg_wait = np.mean(utilization) * 30  # Max 30 min wait
            self.wait_times.append(avg_wait)
            
            step += 1
            
            # Progress update
            if verbose and step % 100 == 0:
                elapsed = time.time() - total_start
                steps_per_sec = step / elapsed
                eta = (self.max_steps - step) / steps_per_sec if steps_per_sec > 0 else 0
                
                print(f"Step {step:4d}/{self.max_steps} | "
                      f"Grid: {env.grid_load:.1%} | "
                      f"Avg Price: ${np.mean(env.station_prices):.2f} | "
                      f"Speed: {steps_per_sec:.1f} steps/s | "
                      f"ETA: {eta:.0f}s")
        
        total_time = time.time() - total_start
        
        # Compile results
        results = self._compile_results(total_time, step)
        
        # Print summary
        self._print_summary(results)
        
        return results
    
    def _compile_results(self, total_time: float, total_steps: int) -> Dict:
        """Compile test results"""
        return {
            "config": {
                "num_evs": self.num_evs,
                "num_stations": self.num_stations,
                "num_cpos": self.num_cpos,
                "max_steps": self.max_steps
            },
            "performance": {
                "total_time_seconds": total_time,
                "total_steps": total_steps,
                "avg_step_time_ms": np.mean(self.step_times) * 1000,
                "max_step_time_ms": np.max(self.step_times) * 1000,
                "min_step_time_ms": np.min(self.step_times) * 1000,
                "steps_per_second": total_steps / total_time
            },
            "grid": {
                "avg_load": np.mean(self.grid_loads),
                "max_load": np.max(self.grid_loads),
                "min_load": np.min(self.grid_loads),
                "load_variance": np.var(self.grid_loads),
                "time_above_80_percent": sum(1 for l in self.grid_loads if l > 0.8) / len(self.grid_loads) * 100
            },
            "pricing": {
                "avg_price": np.mean(self.avg_prices),
                "max_price": np.max(self.avg_prices),
                "min_price": np.min(self.avg_prices),
                "price_variance": np.var(self.avg_prices)
            },
            "revenue": {
                "total": self.total_revenue[-1] if self.total_revenue else 0,
                "avg_per_step": np.mean(np.diff([0] + self.total_revenue)) if len(self.total_revenue) > 1 else 0
            },
            "utilization": {
                "avg_station_utilization": np.mean([np.mean(u) for u in self.station_utilization]),
                "max_station_utilization": np.max([np.max(u) for u in self.station_utilization]),
                "avg_wait_time_minutes": np.mean(self.wait_times)
            },
            "timestamp": datetime.now().isoformat()
        }
    
    def _print_summary(self, results: Dict):
        """Print results summary"""
        print(f"\n{'='*60}")
        print("STRESS TEST RESULTS")
        print(f"{'='*60}")
        
        perf = results["performance"]
        print(f"\n[PERFORMANCE]")
        print(f"   Total Time:      {perf['total_time_seconds']:.2f} seconds")
        print(f"   Steps Completed: {perf['total_steps']:,}")
        print(f"   Throughput:      {perf['steps_per_second']:.1f} steps/second")
        print(f"   Avg Step Time:   {perf['avg_step_time_ms']:.2f} ms")
        print(f"   Max Step Time:   {perf['max_step_time_ms']:.2f} ms")
        
        grid = results["grid"]
        print(f"\n[GRID LOAD]")
        print(f"   Average Load:    {grid['avg_load']:.1%}")
        print(f"   Peak Load:       {grid['max_load']:.1%}")
        print(f"   Load Variance:   {grid['load_variance']:.4f}")
        print(f"   Time > 80%:      {grid['time_above_80_percent']:.1f}%")
        
        pricing = results["pricing"]
        print(f"\n[PRICING]")
        print(f"   Avg Price:       ${pricing['avg_price']:.2f}/kWh")
        print(f"   Price Range:     ${pricing['min_price']:.2f} - ${pricing['max_price']:.2f}")
        
        util = results["utilization"]
        print(f"\n[UTILIZATION]")
        print(f"   Avg Station Use: {util['avg_station_utilization']:.1%}")
        print(f"   Max Station Use: {util['max_station_utilization']:.1%}")
        print(f"   Avg Wait Time:   {util['avg_wait_time_minutes']:.1f} minutes")
        
        rev = results["revenue"]
        print(f"\n[REVENUE]")
        print(f"   Total Revenue:   ${rev['total']:.2f}")
        print(f"   Avg Per Step:    ${rev['avg_per_step']:.2f}")
        
        print(f"\n{'='*60}")
        
        # Pass/Fail criteria
        passed = True
        issues = []
        
        if perf['avg_step_time_ms'] > 100:
            passed = False
            issues.append(f"Step time too high: {perf['avg_step_time_ms']:.0f}ms > 100ms")
        
        if grid['time_above_80_percent'] > 30:
            passed = False
            issues.append(f"Grid overload too frequent: {grid['time_above_80_percent']:.0f}% > 30%")
        
        if util['avg_wait_time_minutes'] > 15:
            passed = False
            issues.append(f"Wait times too long: {util['avg_wait_time_minutes']:.0f}min > 15min")
        
        if passed:
            print("[PASSED] STRESS TEST SUCCESSFUL")
        else:
            print("[FAILED] STRESS TEST FAILED")
            for issue in issues:
                print(f"   - {issue}")
        
        print(f"{'='*60}\n")
    
    def plot_results(self, save_path: str = None):
        """Plot stress test results"""
        fig, axes = plt.subplots(2, 3, figsize=(16, 10))
        
        # Step times
        ax = axes[0, 0]
        ax.plot(self.step_times, alpha=0.7)
        ax.axhline(y=0.1, color='r', linestyle='--', label='100ms threshold')
        ax.set_title("Step Execution Time")
        ax.set_xlabel("Step")
        ax.set_ylabel("Time (seconds)")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Grid load
        ax = axes[0, 1]
        ax.plot(self.grid_loads, alpha=0.7, color='green')
        ax.axhline(y=0.6, color='blue', linestyle='--', label='Target (60%)')
        ax.axhline(y=0.8, color='orange', linestyle='--', label='Warning (80%)')
        ax.axhline(y=0.85, color='red', linestyle='--', label='Critical (85%)')
        ax.set_title("Grid Load Over Time")
        ax.set_xlabel("Step")
        ax.set_ylabel("Load %")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # Average prices
        ax = axes[0, 2]
        ax.plot(self.avg_prices, alpha=0.7, color='purple')
        ax.set_title("Average Price Over Time")
        ax.set_xlabel("Step")
        ax.set_ylabel("Price ($/kWh)")
        ax.grid(True, alpha=0.3)
        
        # Cumulative revenue
        ax = axes[1, 0]
        ax.plot(self.total_revenue, color='gold')
        ax.set_title("Cumulative Revenue")
        ax.set_xlabel("Step")
        ax.set_ylabel("Revenue ($)")
        ax.grid(True, alpha=0.3)
        
        # Station utilization heatmap (last 100 steps)
        ax = axes[1, 1]
        util_matrix = np.array(self.station_utilization[-100:]).T
        im = ax.imshow(util_matrix, aspect='auto', cmap='RdYlGn_r')
        ax.set_title("Station Utilization (Last 100 Steps)")
        ax.set_xlabel("Step")
        ax.set_ylabel("Station")
        plt.colorbar(im, ax=ax, label='Utilization')
        
        # Wait time distribution
        ax = axes[1, 2]
        ax.hist(self.wait_times, bins=30, alpha=0.7, color='coral')
        ax.axvline(x=np.mean(self.wait_times), color='r', linestyle='--', 
                   label=f'Mean: {np.mean(self.wait_times):.1f}min')
        ax.set_title("Wait Time Distribution")
        ax.set_xlabel("Wait Time (minutes)")
        ax.set_ylabel("Frequency")
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=150)
            print(f"[*] Saved results plot to {save_path}")
        else:
            plt.show()
    
    def save_results(self, results: Dict, path: str = "stress_test_results.json"):
        """Save results to JSON file"""
        with open(path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"[*] Saved results to {path}")


def main():
    parser = argparse.ArgumentParser(description="Stress test IEVC-eco system")
    parser.add_argument("--evs", type=int, default=1000, help="Number of EVs")
    parser.add_argument("--stations", type=int, default=50, help="Number of stations")
    parser.add_argument("--cpos", type=int, default=10, help="Number of CPOs")
    parser.add_argument("--steps", type=int, default=576, help="Simulation steps")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--plot", action="store_true", help="Show results plot")
    parser.add_argument("--save-plot", type=str, default=None, help="Save plot path")
    parser.add_argument("--save-results", type=str, default=None, help="Save results JSON path")
    
    args = parser.parse_args()
    
    # Create and run stress test
    test = StressTest(
        num_evs=args.evs,
        num_stations=args.stations,
        num_cpos=args.cpos,
        max_steps=args.steps,
        seed=args.seed
    )
    
    results = test.run(verbose=True)
    
    # Save and plot if requested
    if args.save_results:
        test.save_results(results, args.save_results)
    
    if args.plot or args.save_plot:
        test.plot_results(args.save_plot)


if __name__ == "__main__":
    main()
