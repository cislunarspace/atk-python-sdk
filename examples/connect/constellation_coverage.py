"""
ATK Connect Mode — Walker Constellation Coverage Example

Demonstrates creating a 60-satellite Walker Delta constellation and
computing ground coverage statistics.

Requirements:
- ATK software must be running and listening on 127.0.0.1:6655

Usage:
    python examples/connect/constellation_coverage.py
"""

from atk.connect import connect


def main() -> None:
    with connect() as atk:
        print("[1] Connected to ATK")

        # ---------------------------------------------------------------
        # Create scenario
        # ---------------------------------------------------------------
        scenario = atk.create_scenario("WalkerCoverage")
        scenario.set_analysis_period(
            "1 Jan 2024 00:00:00.000",
            "2 Jan 2024 00:00:00.000",
        )
        print("[2] Scenario created: WalkerCoverage")

        # ---------------------------------------------------------------
        # Create ground facility
        # ---------------------------------------------------------------
        facility_path = "*/Facility/GroundStation"
        atk.send("New", facility_path, "")
        atk.send(
            "SetPosition",
            facility_path,
            ' LLA 40.0 -74.0 0.0',
        )
        print("[3] Ground station created at (40°N, 74°W)")

        # ---------------------------------------------------------------
        # Build Walker constellation
        # ---------------------------------------------------------------
        walker = atk.constellation_builder("Starlink")
        walker.walker_delta(
            num_satellites=60,
            num_planes=6,
            inc=53.0,
            alt=550.0,
        )
        walker.set_propagator("PropagatorSGP4")
        walker.build()
        print(f"[4] Walker Delta constellation built: {walker}")

        # ---------------------------------------------------------------
        # Create coverage definition
        # ---------------------------------------------------------------
        cov = atk.create_coverage("GroundCoverage")
        cov.add_facility("*/Facility/GroundStation")
        cov.set_grid_resolution(lat_step=1.0, lon_step=1.0)
        cov.set_fom("SimpleAER")

        # Add all constellation satellites as assets
        for sat_idx in range(60):
            plane = sat_idx // 10
            sat_in_plane = sat_idx % 10
            sat_path = f"*/Constellation/Starlink/Satellite/Starlink_P{plane}_S{sat_in_plane}"
            cov.add_asset(sat_path)

        print("[5] Coverage definition configured")

        # ---------------------------------------------------------------
        # Compute coverage statistics
        # ---------------------------------------------------------------
        stats = cov.compute_stats(time_period="*")
        print(f"\n[6] Coverage Statistics:")
        print(f"    Access count:        {stats.access_count}")
        print(f"    Total access time:   {stats.total_access_time:.2f} s")
        print(f"    Mean access duration: {stats.mean_access_duration:.2f} s")

        # ---------------------------------------------------------------
        # Run MCS for all satellites (parallel)
        # ---------------------------------------------------------------
        results = walker.run_all(max_workers=8)
        success_count = sum(1 for v in results.values() if v)
        print(f"\n[7] MCS run: {success_count}/{len(results)} satellites succeeded")

        # ---------------------------------------------------------------
        # Save scenario
        # ---------------------------------------------------------------
        scenario.save()
        print("[8] Scenario saved")
        print("\nWalker constellation coverage example completed!")


if __name__ == "__main__":
    main()
