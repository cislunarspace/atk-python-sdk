# 故障排查

## Connect 模式问题

### 连接被拒绝

**错误信息**：
```
ATKConnectionError: [127.0.0.1:6655] Failed after 3 attempts
```

**原因**：ATK 软件未运行或未监听指定端口。

**解决方法**：
1. 确保 ATK 软件已启动
2. 检查 ATK 的 Connect 设置中端口是否为 6655
3. 确认防火墙未阻止该端口

### 命令返回 NACK

**错误信息**：
```
ATKCommandError: Command 'New' failed for '*/Satellite/Sat1'
```

**原因**：命令执行失败，可能原因：
- 对象已存在
- 路径格式错误
- 参数无效

**解决方法**：
1. 检查对象是否已存在：`Unload / */Satellite/Sat1`
2. 验证路径格式是否正确
3. 查看 ATK 文档中命令的正确用法

### 场景无法保存

**错误信息**：
```
ATKScenarioError: Save failed
```

**可能原因**：
- 保存路径无效
- 文件被锁定
- 权限不足

**解决方法**：
1. 使用有效路径：`Save / * "C:/temp/scenario.xml"`
2. 关闭 ATK 中打开的场景
3. 检查文件权限

### 设置属性无效

ATK Python 客户端界面属性窗口不具备实时更新功能。

**解决方法**：
设置属性后，重新打开对象属性界面查看设置结果。

## Component 模式问题

### ATKComponentPythonModule 找不到

**错误信息**：
```
ATKComponentError: ATKComponentPythonModule not found
```

**解决方法**：

1. **方法一**：复制文件到项目
   ```bash
   # 从 ATK 安装目录复制
   cp ATK/ATK-v4.0/ATKComponentPythonModule.py vendored/
   cp ATK/ATK-v4.0/_ATKComponentPythonModule.pyd vendored/
   ```

2. **方法二**：设置 ATK_ROOT
   ```bash
   set ATK_ROOT=C:\Program Files\ATK\ATK-v4.0
   ```

### DLL 加载失败

**错误信息**：
```
ImportError: DLL load failed
```

**可能原因**：
- ATK DLL 不在系统 PATH 中
- DLL 版本不匹配
- 缺少依赖

**解决方法**：
1. 将 ATK DLL 所在目录添加到系统 PATH
2. 确保使用与 ATK 版本匹配的 DLL

### 场景操作失败

**可能错误**：
- `NewScenario` 失败：场景已存在
- `SaveScenario` 失败：无权限或路径无效

**解决方法**：
```python
# 先关闭已存在的场景
session.close_scenario()

# 然后新建
scenario = session.new_scenario('MyScenario')
```

## 轨道计算问题

### 轨道不闭合

**现象**：传播后卫星状态与初始状态不一致。

**可能原因**：
- 传播步长过大
- 传播器精度不足
- 时间格式错误

**解决方法**：
1. 减小传播步长
2. 使用更高精度的传播器（如 HPOP）
3. 检查时间字符串格式

### 半长轴变为负数

**现象**：设置正半长轴，传播后变为负值。

**原因**：离心率 ≥ 1 或时间超出有效范围。

**解决方法**：
1. 确保离心率 `0 ≤ ecc < 1`
2. 检查分析时段设置

## 时间格式问题

### 时间解析失败

**错误信息**：
```
ATKValueError: Unrecognized time format: '2023/07/29'
```

**原因**：ATK 不支持该时间格式。

**解决方法**：使用支持的时间格式：
```python
# 正确
parse_atk_time("29 Jul 2023 09:19:01.000")
parse_atk_time("29 Jul 2023")

# 错误
parse_atk_time("2023/07/29")
parse_atk_time("2023-07-29")
```

## 地面站和传感器问题

### 地面站创建失败

**错误信息**：
```
ATKCommandError: Command 'New' failed for '/'
```

**可能原因**：
- 地面站名称包含特殊字符
- ATK 场景未加载

**解决方法**：
1. 使用纯字母数字名称
2. 确保已创建场景：`atk.create_scenario('MyScenario')`

### 传感器视场设置无效

**现象**：设置视场后传感器行为不符合预期。

**可能原因**：
- 欧拉角转序不正确
- 俯仰角/方位角范围无效

**解决方法**：
```python
# 确保角度范围合理
sensor.define_conical(el_start=5, el_end=85, az_start=0, az_end=360)
# 检查欧拉角转序
sensor.point_fixed_euler(sequence=123, a1=180, a2=0, a3=0)
```

### TLE 格式错误

**错误信息**：
```
ATKCommandError: Command 'SetState' failed
```

**可能原因**：TLE 行长度不正确（应为 69 字符）。

**解决方法**：
```python
# 确保 TLE 行格式正确（69 字符）
line1 = '1 25544U 98067A   24001.50000000  .00016717  00000-0  10270-3 0  9000'
line2 = '2 25544  51.6400 208.9163 0006703  44.2800 315.9700 15.49000000400000'
sat.set_state_tle(line1=line1, line2=line2)
```

## 报告生成问题

### 报告返回空

**可能原因**：
- 分析时段内无数据
- 对象路径错误
- 报告类型不支持该对象

**解决方法**：
1. 检查分析时段是否包含仿真时间
2. 验证对象路径格式
3. 确认报告类型是否适用

### 报告返回空 DataFrame

**现象**：`to_dataframe()` 返回空 DataFrame。

**可能原因**：
- `atkConnect` 返回了 `str` 而非 `CMDRESULT`（SWIG DLL 行为不一致）
- 分析时段内无数据

**解决方法**：
1. 检查 `result.data` 是否为空
2. 确认分析时段包含仿真时间
3. 确保已运行 MCS 或传播

### CMDRESULT 返回类型异常

**现象**：`send()` 返回原始字符串而非预期的 `CMDRESULT`。

**原因**：SWIG DLL 的 `atkConnect()` 可能返回 `str` 或 `CMDRESULT`，取决于 ATK 版本和命令类型。

**解决方法**：
SDK 的 `send()` 方法已处理这种情况。如果直接处理 `send()` 返回值：

```python
result = atk.send('SomeCommand', '*', '')
if isinstance(result, str):
    # 字符串响应
    pass
else:
    # CMDRESULT 对象
    data = result.m_vectData
```

**可能原因**：
- 报告样式名称错误
- 缺少必要参数

**解决方法**：查看 ATK 安装目录下的 `AstroData/ReportStyle` 文件夹获取正确的报告名称。

## 常见错误代码

| 错误代码 | 说明 | 解决方法 |
|----------|------|----------|
| `NACK` | 命令被拒绝 | 检查命令格式和参数 |
| `ERROR` | 执行错误 | 查看详细错误信息 |
| `FAIL` | 操作失败 | 检查对象状态 |
| `FALSE` | 返回 false | 检查条件是否满足 |

## 获取帮助

1. 查看 ATK 官方文档中的 Connect 命令库
2. 检查 [ATK 对象模型](../background/atk-object-model.md)
3. 参考 [ATK Connect 命令](../reference/atk-commands.md)
