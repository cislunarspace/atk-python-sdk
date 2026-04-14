"""
ATK Component Mode — Hohmann Transfer Example

Demonstrates a two-impulsive-burn Hohmann transfer using the
Component mode API (direct DLL, no ATK window required).

Requirements:
- Run within ATK's embedded Python interpreter, OR
- Copy ATKComponentPythonModule.py and _ATKComponentPythonModule.pyd
  to this project directory and set ATK_ROOT environment variable.

Usage (inside ATK's Python environment):
    python examples/component/hohmann_transfer.py
"""

from atk.component import component_session


def main() -> None:
    with component_session() as session:
        print("[1] Component session started")

        # ---------------------------------------------------------------
        # Create scenario
        # ---------------------------------------------------------------
        scenario = session.new_scenario("HohmannTransferComponent")
        scenario.set_analysis_period(
            "1 Jan 2024 00:00:00.000",
            "2 Jan 2024 00:00:00.000",
        )
        print(f"[2] Scenario created: {scenario.name}")

        # ---------------------------------------------------------------
        # Create satellite
        # ---------------------------------------------------------------
        sat_obj = scenario.create_satellite("TransferVehicle")
        print(f"[3] Satellite created: {sat_obj.GetInstanceName()}")

        # ---------------------------------------------------------------
        # Import and use SatelliteBuilder
        # ---------------------------------------------------------------
        from atk.component.satellite import SatelliteBuilder
        from atk.component.mcs import McsBuilder

        sat = SatelliteBuilder(sat_obj)
        sat.set_propagator_type("PropagatorAstromaster")
        print("[4] Propagator set: Astromaster")

        # ---------------------------------------------------------------
        # Build MCS
        # ---------------------------------------------------------------
        driver = sat.get_mcs_driver()
        mcs = McsBuilder(driver)

        mcs.initial_state_keplerian(
            sma=6678.0,
            ecc=0.0,
            inc=0.0,
            raan=0.0,
            argp=0.0,
            ta=0.0,
            epoch="1 Jan 2024 00:00:00.000",
        )
        print("[5] Initial state set")

        mcs.propagate_duration(duration_seconds=5444.0, time_step=60.0)
        print("[6] Coast segment added")

        mcs.impulsive_burn(dv=[0.1, 0.0, 0.0], direction="Velocity")
        print("[7] Hohmann burn 1 added")

        mcs.propagate_duration(duration_seconds=5444.0, time_step=60.0)
        mcs.impulsive_burn(dv=[0.1, 0.0, 0.0], direction="Velocity")
        print("[8] Hohmann burn 2 added")

        # ---------------------------------------------------------------
        # Run MCS
        # ---------------------------------------------------------------
        mcs.run()
        mcs.apply_changes()
        print("[9] MCS completed")

        # ---------------------------------------------------------------
        # Save scenario
        # ---------------------------------------------------------------
        scenario.save()
        print("[10] Scenario saved")
        print("\nComponent mode Hohmann transfer example completed!")
