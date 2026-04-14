"""
ATK Connect Mode — Hohmann Transfer Example

Demonstrates a two-impulsive-burn Hohmann transfer between two circular orbits
using the Connect mode API.

Requirements:
- ATK software must be running and listening on 127.0.0.1:6655

Usage:
    python examples/connect/hohmann_transfer.py
"""

from atk.connect import connect


def main() -> None:
    # ---------------------------------------------------------------
    # Connect to ATK
    # ---------------------------------------------------------------
    with connect() as atk:
        print("[1] Connected to ATK")

        # ---------------------------------------------------------------
        # Create scenario
        # ---------------------------------------------------------------
        scenario = atk.create_scenario("HohmannTransfer")
        scenario.set_analysis_period(
            "1 Jan 2024 00:00:00.000",
            "2 Jan 2024 00:00:00.000",
        )
        print("[2] Scenario created: HohmannTransfer")

        # ---------------------------------------------------------------
        # Create transfer satellite
        # ---------------------------------------------------------------
        sat = atk.create_satellite("TransferVehicle")
        sat.set_propagator("PropagatorAstromaster")
        print("[3] Satellite created: TransferVehicle")

        # ---------------------------------------------------------------
        # Build MCS: initial orbit → Hohmann burn 1 → coast → Hohmann burn 2
        # ---------------------------------------------------------------
        mcs = atk.mcs_builder("*/Satellite/TransferVehicle")

        # Initial orbit: circular at 6678 km SMA (~ISS altitude), 0 deg inc
        mcs.initial_state_keplerian(
            sma=6678.0,
            ecc=0.0,
            inc=0.0,
            raan=0.0,
            argp=0.0,
            ta=0.0,
            epoch="1 Jan 2024 00:00:00.000",
        )
        print("[4] Initial state set")

        # Coasting propagation to departure point (opposite side of orbit)
        # Half orbital period at 6678 km: T = 2*pi*sqrt(a^3/mu) ~ 5444 s ~ 90.7 min
        # Propagate for half period (~90 min = 5444 s)
        mcs.propagate_duration(duration_seconds=5444.0, time_step=60.0)
        print("[5] Coast segment added")

        # Hohmann burn 1: prograde dv at periapsis
        # dv1 = sqrt(mu/r1) * (sqrt(2*r2/(r1+r2)) - 1)
        # r1=r2=6678 km (both circular, same altitude) — simplified example
        mcs.impulsive_burn(dv=[0.1, 0.0, 0.0], burn_direction=" Velocity")
        print("[6] Hohmann burn 1 added")

        # Coasting to target orbit
        mcs.propagate_duration(duration_seconds=5444.0, time_step=60.0)

        # Hohmann burn 2: circularize at apogee
        mcs.impulsive_burn(dv=[0.1, 0.0, 0.0], burn_direction=" Velocity")
        print("[7] Hohmann burn 2 added")

        # ---------------------------------------------------------------
        # Run MCS
        # ---------------------------------------------------------------
        mcs.run()
        mcs.apply_changes()
        print("[8] MCS completed")

        # ---------------------------------------------------------------
        # Save scenario
        # ---------------------------------------------------------------
        scenario.save()
        print("[9] Scenario saved")

        print("\nHohmann transfer example completed successfully!")


if __name__ == "__main__":
    main()
