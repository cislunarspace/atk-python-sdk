"""
ATK 提供的 SWIG 绑定（vendored）。

此包重新导出原始的 SWIG 生成的 Connect 绑定
(ATKConnectModule)，以便 atk.connect.session 可以导入它们。

此目录中的 ATK 提供文件：
    ATKConnectModule.py       — SWIG Python 封装
    _ATKConnectModule.pyd     — Windows 扩展
    _ATKConnectModule.so      — Linux x64 扩展
    _ATKConnectModule.cpython-38-aarch64-linux-gnu.so  — Linux ARM64 扩展
"""

import os
import sys

# 确保此目录在 sys.path 中，以便原始模块导入正常工作
_vendored_dir = os.path.dirname(__file__)
if _vendored_dir not in sys.path:
    sys.path.insert(0, _vendored_dir)

from ATKConnectModule import (
    InitConnector,
    atkOpen,
    atkConnect,
    atkClose,
    atkConnectEx,
    atkExecuteScript,
    atkExecuteCommand,
    CMDRESULT,
)

__all__ = [
    "InitConnector",
    "atkOpen",
    "atkConnect",
    "atkClose",
    "atkConnectEx",
    "atkExecuteScript",
    "atkExecuteCommand",
    "CMDRESULT",
]
