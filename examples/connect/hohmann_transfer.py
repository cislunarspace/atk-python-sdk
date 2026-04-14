"""
ATK Connect 模式 — 霍曼转移示例

演示使用 Connect 模式 API 在两个圆轨道之间执行双脉冲霍曼转移。

运行要求：
- ATK 软件必须正在运行并监听 127.0.0.1:6655

用法：
    python examples/connect/hohmann_transfer.py
"""

from atk.connect import connect


def main() -> None:
    # ---------------------------------------------------------------
    # 连接到 ATK
    # ---------------------------------------------------------------
    with connect() as atk:
        print("[1] 已连接到 ATK")

        # ---------------------------------------------------------------
        # 创建场景
        # ---------------------------------------------------------------
        scenario = atk.create_scenario("HohmannTransfer")
        scenario.set_analysis_period(
            "1 Jan 2024 00:00:00.000",
            "2 Jan 2024 00:00:00.000",
        )
        print("[2] 场景已创建: HohmannTransfer")

        # ---------------------------------------------------------------
        # 创建转移卫星
        # ---------------------------------------------------------------
        sat = atk.create_satellite("TransferVehicle")
        sat.set_propagator("PropagatorAstromaster")
        sat.set_keplerian(sma=6678.0, ecc=0.0, inc=0.0, raan=0.0, argp=0.0, ta=0.0)
        print("[3] 卫星已创建: TransferVehicle")

        # ---------------------------------------------------------------
        # 构建 MCS：初始轨道 → 霍曼脉冲 1 → 滑行 → 霍曼脉冲 2
        # ---------------------------------------------------------------
        mcs = atk.mcs_builder("*/Satellite/TransferVehicle")

        # 初始轨道：6678 km SMA 的圆轨道（约 ISS 高度），0° 倾角
        mcs.initial_state_keplerian(
            sma=6678.0,
            ecc=0.0,
            inc=0.0,
            raan=0.0,
            argp=0.0,
            ta=0.0,
            epoch="1 Jan 2024 00:00:00.000",
        )
        print("[4] 初始状态已设置")

        # 滑行传播到出发点（轨道对面）
        # 6678 km 处的半轨道周期：T = 2*pi*sqrt(a^3/mu) ≈ 5444 s ≈ 90.7 min
        # 传播半个周期（约 90 分钟 = 5444 秒）
        mcs.propagate_duration(duration_seconds=5444.0, time_step=60.0)
        print("[5] 滑行段已添加")

        # 霍曼脉冲 1：在近地点沿速度方向施加 dv
        # dv1 = sqrt(mu/r1) * (sqrt(2*r2/(r1+r2)) - 1)
        # r1=r2=6678 km（均为圆轨道，相同高度）— 简化示例
        mcs.impulsive_burn(dv=[0.1, 0.0, 0.0], burn_direction=" Velocity")
        print("[6] 霍曼脉冲 1 已添加")

        # 滑行到目标轨道
        mcs.propagate_duration(duration_seconds=5444.0, time_step=60.0)

        # 霍曼脉冲 2：在远地点圆化
        mcs.impulsive_burn(dv=[0.1, 0.0, 0.0], burn_direction=" Velocity")
        print("[7] 霍曼脉冲 2 已添加")

        # ---------------------------------------------------------------
        # 运行 MCS
        # ---------------------------------------------------------------
        mcs.run()
        mcs.apply_changes()
        print("[8] MCS 已完成")

        # ---------------------------------------------------------------
        # 保存场景
        # ---------------------------------------------------------------
        scenario.save()
        print("[9] 场景已保存")

        print("\n霍曼转移示例已成功完成！")


if __name__ == "__main__":
    main()
