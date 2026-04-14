"""
ATK Connect 模式 — Walker 星座覆盖示例

演示创建 60 颗卫星的 Walker Delta 星座并计算地面覆盖统计。

运行要求：
- ATK 软件必须正在运行并监听 127.0.0.1:6655

用法：
    python examples/connect/constellation_coverage.py
"""

from atk.connect import connect


def main() -> None:
    with connect() as atk:
        print("[1] 已连接到 ATK")

        # ---------------------------------------------------------------
        # 创建场景
        # ---------------------------------------------------------------
        scenario = atk.create_scenario("WalkerCoverage")
        scenario.set_analysis_period(
            "1 Jan 2024 00:00:00.000",
            "2 Jan 2024 00:00:00.000",
        )
        print("[2] 场景已创建: WalkerCoverage")

        # ---------------------------------------------------------------
        # 创建地面站
        # ---------------------------------------------------------------
        # ATK 格式：obj='*', param=' Facility/{name}'
        atk.send("New", "*", " Facility/GroundStation")
        # ATK 格式：obj='*/Facility/{name}', param=' Geodetic {lat} {lon} {height}'
        atk.send(
            "SetPosition",
            "*/Facility/GroundStation",
            " Geodetic 40.0 -74.0 0.0",
        )
        print("[3] 地面站已创建，位于 (40°N, 74°W)")

        # ---------------------------------------------------------------
        # 构建 Walker 星座
        # ---------------------------------------------------------------
        walker = atk.constellation_builder("Starlink")
        walker.walker_delta(
            num_satellites=60,
            num_planes=6,
            inc=53.0,
            alt=550.0,
        )
        walker.set_propagator("PropagatorTwoBody")
        walker.build()
        print(f"[4] Walker Delta 星座已构建: {walker}")

        # ---------------------------------------------------------------
        # 创建覆盖定义
        # ---------------------------------------------------------------
        cov = atk.create_coverage("GroundCoverage")
        cov.add_facility("*/Facility/GroundStation")
        cov.set_grid_resolution(lat_step=1.0, lon_step=1.0)
        cov.set_fom("SimpleAER")

        # 将所有星座卫星添加为资产
        for sat_idx in range(60):
            plane = sat_idx // 10
            sat_in_plane = sat_idx % 10
            sat_path = f"*/Constellation/Starlink/Satellite/Starlink_P{plane}_S{sat_in_plane}"
            cov.add_asset(sat_path)

        print("[5] 覆盖定义已配置")

        # ---------------------------------------------------------------
        # 计算覆盖统计
        # ---------------------------------------------------------------
        stats = cov.compute_stats(time_period="*")
        print(f"\n[6] 覆盖统计:")
        print(f"    访问次数:        {stats.access_count}")
        print(f"    总访问时间:      {stats.total_access_time:.2f} s")
        print(f"    平均访问时长:    {stats.mean_access_duration:.2f} s")

        # ---------------------------------------------------------------
        # 运行所有卫星的 MCS（串行）
        # ---------------------------------------------------------------
        results = walker.run_all()
        success_count = sum(1 for v in results.values() if v)
        print(f"\n[7] MCS 运行: {success_count}/{len(results)} 颗卫星成功")

        # ---------------------------------------------------------------
        # 保存场景
        # ---------------------------------------------------------------
        scenario.save()
        print("[8] 场景已保存")
        print("\nWalker 星座覆盖示例已完成！")


if __name__ == "__main__":
    main()
