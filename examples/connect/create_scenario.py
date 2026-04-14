from atk.connect import connect

# 使用上下文管理器
with connect() as atk:
    # 新建场景
    scenario = atk.create_scenario('MyScenario')
    scenario.set_analysis_period('1 Jan 2024 00:00:00.000', '7 Jan 2024 00:00:00.000')

    # 新建地面站
    facility = atk.create_facility('Beijing', lat=39.9, lon=116.4, height=50)
    facility.set_color(5)

    # 在地面站下创建传感器
    sensor = facility.create_sensor(
        'Sensor1',
        el_start=5,          # 俯仰角起始 (deg)
        el_end=85,           # 俯仰角终止 (deg)
        az_start=0,          # 方位角起始 (deg)
        az_end=360,          # 方位角终止 (deg)
        max_range=2000,      # 最大作用距离 (km)
    )

    # 新建卫星（开普勒元素方式）
    sat = atk.create_satellite('Sat1')
    sat.set_propagator('PropagatorTwoBody')
    sat.set_keplerian(
        sma=7100,      # 半长轴 (km)
        ecc=0.001,     # 离心率
        inc=30,        # 倾角 (deg)
        raan=0,        # 升交点赤经 (deg)
        argp=0,        # 近地点幅角 (deg)
        ta=0           # 真近点角 (deg)
    )
    sat.set_color(12)

    # 保存场景
    scenario.save()
