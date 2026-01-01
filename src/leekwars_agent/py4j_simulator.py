"""Fast fight simulator using Py4J to keep JVM running.

This provides ~50x speedup over subprocess by avoiding JVM startup overhead.

Usage:
    # Start Java gateway (run once)
    cd tools/leek-wars-generator
    java -cp generator.jar com.leekwars.Py4JGateway

    # Then use from Python
    from leekwars_agent.py4j_simulator import Py4JSimulator
    sim = Py4JSimulator()
    outcome = sim.run_1v1("fighter_v1.leek", "fighter_v1.leek")
"""

import json
import subprocess
import time
import atexit
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from py4j.java_gateway import JavaGateway, GatewayParameters

from .simulator import FightOutcome, GENERATOR_PATH


@dataclass
class Py4JSimulator:
    """
    Fast simulator using Py4J connection to running JVM.

    Keeps JVM warm for fast repeated simulations (~50 fights/sec).
    """

    gateway: JavaGateway | None = None
    _process: subprocess.Popen | None = None

    def __post_init__(self):
        self._connect()

    def _connect(self, max_retries: int = 3) -> None:
        """Connect to existing gateway or start one."""
        for attempt in range(max_retries):
            try:
                self.gateway = JavaGateway(
                    gateway_parameters=GatewayParameters(port=25333)
                )
                # Test connection
                _ = self.gateway.entry_point
                return
            except Exception:
                if attempt == 0:
                    # Try starting the gateway
                    self._start_gateway()
                    time.sleep(2)  # Wait for JVM startup
                else:
                    time.sleep(1)

        raise ConnectionError(
            "Could not connect to Py4J gateway. "
            "Start it manually: cd tools/leek-wars-generator && "
            "java -cp generator.jar com.leekwars.Py4JGateway"
        )

    def _start_gateway(self) -> None:
        """Start the Java gateway process."""
        print("Starting Py4J gateway...")
        self._process = subprocess.Popen(
            ["java", "-cp", "generator.jar", "com.leekwars.Py4JGateway"],
            cwd=GENERATOR_PATH,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        atexit.register(self._stop_gateway)

    def _stop_gateway(self) -> None:
        """Stop the Java gateway process."""
        if self._process:
            self._process.terminate()
            self._process = None

    def run_1v1(
        self,
        ai1: str,
        ai2: str,
        level: int = 1,
        seed: int = 0,
    ) -> FightOutcome:
        """
        Run a 1v1 fight.

        Args:
            ai1: Path to first AI file (relative to generator dir)
            ai2: Path to second AI file
            level: Level for both leeks
            seed: Random seed (0 for random)

        Returns:
            FightOutcome with winner, turns, actions
        """
        if not self.gateway:
            self._connect()

        start = time.perf_counter()

        # Call Java
        result_json = self.gateway.entry_point.runFight1v1(ai1, ai2, level, seed)
        duration_ms = (time.perf_counter() - start) * 1000

        # Parse result
        output = json.loads(result_json)

        return FightOutcome(
            winner=output.get("winner", -1),
            turns=output.get("turns", 0),
            actions=output.get("fight", {}).get("actions", []),
            duration_ms=duration_ms,
            raw_output=output,
        )

    def close(self) -> None:
        """Close the gateway connection."""
        if self.gateway:
            self.gateway.close()
            self.gateway = None
        self._stop_gateway()


def benchmark(n_fights: int = 100) -> dict[str, float]:
    """Benchmark Py4J simulator throughput."""
    sim = Py4JSimulator()

    # Warmup
    for _ in range(5):
        sim.run_1v1("fighter_v1.leek", "fighter_v1.leek", seed=0)

    start = time.perf_counter()
    for i in range(n_fights):
        sim.run_1v1("fighter_v1.leek", "fighter_v1.leek", seed=i)
    total_time = time.perf_counter() - start

    sim.close()

    return {
        "fights": n_fights,
        "total_seconds": total_time,
        "fights_per_second": n_fights / total_time,
        "ms_per_fight": (total_time / n_fights) * 1000,
    }


if __name__ == "__main__":
    print("Testing Py4J simulator...")

    try:
        sim = Py4JSimulator()
        outcome = sim.run_1v1("fighter_v1.leek", "fighter_v1.leek", seed=42)
        print(f"Test fight: winner={outcome.winner}, turns={outcome.turns}")

        print("\nBenchmarking (50 fights)...")
        results = benchmark(n_fights=50)
        print(f"Results: {results['fights_per_second']:.1f} fights/sec")
        print(f"         {results['ms_per_fight']:.1f} ms/fight")

    except ConnectionError as e:
        print(f"Error: {e}")
        print("\nTo start the gateway manually:")
        print("  cd tools/leek-wars-generator")
        print("  java -cp generator.jar com.leekwars.Py4JGateway")
