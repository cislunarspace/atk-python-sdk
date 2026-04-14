"""
ATK Component 模式 — 霍曼转移示例

演示使用 Component 模式 API（直接 DLL，无需 ATK 窗口）
执行双脉冲霍曼转移。

运行要求：
- 在 ATK 的嵌入式 Python 解释器中运行，或
- 将 ATKComponentPythonModule.py 和 _ATKComponentPythonModule.pyd
  复制到此项目目录并设置 ATK_ROOT 环境变量。

用法（在 ATK 的 Python 环境中）：
    python examples/component/hohmann_transfer.py
"""

from atk.component import component_session
from atk.component.scenario import ScenarioBuilder
from atk.component.satellite import SatelliteBuilder
from atk.component.mcs import McsBuilder


def main() -> None:
    with component_session() as session:
        print("[1] Component 会话已启动")

        # ---------------------------------------------------------------
        # 创建场景
        # ---------------------------------------------------------------
        scenario_obj = session.new_scenario("HohmannTransferComponent")
        scenario = ScenarioBuilder(session, scenario_obj)
        scenario.set_analysis_period(
            "1 Jan 2024 00:00:00.000",
            "2 Jan 2024 00:00:00.000",
        )
        print(f"[2] 场景已创建: {scenario.name}")

        # ---------------------------------------------------------------
        # 创建卫星
        # ---------------------------------------------------------------
        sat_obj = scenario.create_satellite("TransferVehicle")
        print(f"[3] 卫星已创建: {sat_obj.GetInstanceName()}")

        # ---------------------------------------------------------------
        # 配置卫星
        # ---------------------------------------------------------------
        sat = SatelliteBuilder(sat_obj)
        sat.set_propagator_type("PropagatorAstromaster")
        print("[4] 传播器已设置: Astromaster")

        # ---------------------------------------------------------------
        # 构建 MCS
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
        print("[5] 初始状态已设置")

        mcs.propagate_duration(duration_seconds=5444.0, time_step=60.0)
        print("[6] 滑行段已添加")

        mcs.impulsive_burn(dv=[0.1, 0.0, 0.0], direction="Velocity")
        print("[7] 霍曼脉冲 1 已添加")

        mcs.propagate_duration(duration_seconds=5444.0, time_step=60.0)
        mcs.impulsive_burn(dv=[0.1, 0.0, 0.0], direction="Velocity")
        print("[8] 霍曼脉冲 2 已添加")

        # ---------------------------------------------------------------
        # 运行 MCS
        # ---------------------------------------------------------------
        mcs.run()
        mcs.apply_changes()
        print("[9] MCS 已完成")

        # ---------------------------------------------------------------
        # 保存场景
        # ---------------------------------------------------------------
        scenario.save()
        print("[10] 场景已保存")
        print("\nComponent 模式霍曼转移示例已完成！")


if __name__ == "__main__":
    main()
