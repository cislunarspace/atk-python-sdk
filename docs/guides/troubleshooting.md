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

### 报告格式不正确

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
