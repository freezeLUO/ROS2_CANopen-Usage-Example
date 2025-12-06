# ROS2 Jazzy MoveIt2 + CANopen 测试项目

本项目演示如何在 ROS2 Jazzy 上使用 `ros2_canopen` 与 MoveIt2 集成，通过虚拟 CAN 总线 (vcan0) 模拟真实 CANopen 硬件控制 Pilz PRBT 机械臂。

## 📋 目录

- [环境要求](#环境要求)
- [安装依赖](#安装依赖)
- [快速开始](#快速开始)
- [项目结构](#项目结构)
- [配置说明](#配置说明)
- [常见问题](#常见问题)
- [参考资料](#参考资料)

## 🔧 环境要求

- **操作系统**: Ubuntu 24.04
- **ROS2 版本**: Jazzy Jalisco
- **必需软件包**:
  - `ros-jazzy-moveit`
  - `ros-jazzy-ros2-canopen` (包括 `canopen_fake_slaves`)
  - `ros-jazzy-ros2-control`
  - `ros-jazzy-ros2-controllers`

## 📦 安装依赖

### 1. 安装 ROS2 Jazzy (如未安装)

```bash
# 参考 ROS2 官方文档安装 Jazzy
```

### 2. 安装必需的 ROS2 软件包

```bash
sudo apt update
sudo apt install -y \
    ros-jazzy-moveit \
    ros-jazzy-ros2-canopen \
    ros-jazzy-canopen-fake-slaves \
    ros-jazzy-ros2-control \
    ros-jazzy-ros2-controllers \
    ros-jazzy-controller-manager \
    can-utils
```

### 3. 编译工作空间

```bash
cd ~/ROS2_jazzy_moveit2_test
colcon build
source install/setup.bash
```

## 🚀 快速开始

### 步骤 1: 设置虚拟 CAN 接口

在运行任何 CANopen 相关程序之前，需要先创建虚拟 CAN 接口：

```bash
# 加载 vcan 内核模块
sudo modprobe vcan

# 创建 vcan0 接口
sudo ip link add dev vcan0 type vcan

# 启动接口
sudo ip link set up vcan0
```

> **提示**: 可以使用提供的 launch 文件自动设置：
> ```bash
> ros2 launch prbt_robot_moveit_config vcan.launch.py
> ```

### 步骤 2: 启动完整演示

使用合并的 launch 文件一键启动所有组件：

```bash
cd ~/ROS2_jazzy_moveit2_test
source install/setup.bash
ros2 launch prbt_robot_moveit_config moveit_ros2canopen_with_fake_slaves.launch.py
```

该命令会按正确顺序启动：
1. RViz2 可视化界面
2. Robot State Publisher
3. MoveGroup 节点
4. CANopen 虚拟从站 (fake_slaves)
5. ros2_control_node (延迟启动，等待从站就绪)
6. 控制器 (joint_state_broadcaster, prbt_group_controller)

### 步骤 3: 在 RViz 中规划和执行

1. 在 RViz 中找到 **MotionPlanning** 插件
2. 在 **Planning** 标签页中拖动交互标记设置目标位姿
3. 点击 **Plan** 规划路径
4. 点击 **Execute** 执行运动

### 🖥️ 无头模式 (Headless Mode)

如果不需要 RViz 可视化界面（适用于 CI/CD、服务器部署、脚本自动化测试），可以使用无头模式：

**终端 1 - 启动系统：**
```bash
ros2 launch prbt_robot_moveit_config moveit_ros2canopen_headless.launch.py
```

**终端 2 - 测试选项：**
```bash
# 方法1: 运行测试脚本 (规划并执行一个简单运动)
python3 src/prbt_robot_moveit_config/scripts/test_moveit_headless.py

# 方法2: 查看关节状态
ros2 topic echo /joint_states --once

# 方法3: 查看控制器状态
ros2 control list_controllers
```

## 📁 项目结构

```
ROS2_jazzy_moveit2_test/
├── src/
│   ├── prbt_robot_moveit_config/     # MoveIt2 配置包
│   │   ├── config/
│   │   │   ├── prbt_canopen.urdf.xacro        # 带 CANopen 硬件的 URDF
│   │   │   ├── prbt_canopen.ros2_control.xacro # ros2_control 配置
│   │   │   ├── prbt_canopen_ros2_controllers.yaml
│   │   │   └── moveit_controllers.yaml
│   │   ├── launch/
│   │   │   ├── moveit_ros2canopen.launch.py   # 仅 MoveIt + CANopen
│   │   │   ├── moveit_ros2canopen_with_fake_slaves.launch.py  # 完整演示 ⭐
│   │   │   ├── moveit_ros2canopen_headless.launch.py  # 无头模式 (无RViz)
│   │   │   └── vcan.launch.py                 # vcan 设置
│   │   └── scripts/
│   │       └── test_moveit_headless.py        # 无头模式测试脚本
│   │
│   ├── prbt_robot_support/           # 机器人支持包
│   │   ├── config/prbt/
│   │   │   ├── bus.yml               # CANopen 总线配置 ⭐
│   │   │   └── prbt_0_1.dcf          # 设备配置文件
│   │   └── launch/
│   │       └── fake_slaves.launch.py # 虚拟从站启动
│   │
│   └── arm_prbt/                     # 机器人 URDF 描述
│
├── build/                            # 编译目录
├── install/                          # 安装目录
└── log/                              # 日志目录
```

## ⚙️ 配置说明

### CANopen 总线配置 (bus.yml)

关键配置参数：

```yaml
master:
    node_id: 1
    boot_timeout: 10000        # Master boot 超时 (ms)

defaults:
    boot_timeout_ms: 5000      # ⭐ 驱动 boot 等待时间 (ms) - 重要！
    position_mode: 8           # 周期同步位置模式（CSP）
    switching_state: 2         # 状态切换
    
nodes:
    joint_1:
        node_id: 3
    joint_2:
        node_id: 4
    # ... joint_3 到 joint_6
```

> **重要**: `boot_timeout_ms` 必须设置足够长 (建议 5000ms)，否则会出现 Boot Timeout 错误。

### 启动顺序说明

CANopen 启动有严格的时序要求：

1. **vcan0 接口** 必须先创建并启动
2. **fake_slaves** 需要先启动并发送 Boot-Up frame
3. **ros2_control_node** 必须在 Boot-Up frame 发送后启动

`moveit_ros2canopen_with_fake_slaves.launch.py` 已通过 `TimerAction` 自动处理启动时序。

## ❗ 常见问题

### 1. Boot Timeout 错误

**症状**:
```
[ERROR] [joint_1]: Boot attempt 1 failed: Boot Timeout: The boot configure process timeout!
```

**解决方案**:
- 确保 `bus.yml` 中设置了 `boot_timeout_ms: 5000`
- 确保使用 `moveit_ros2canopen_with_fake_slaves.launch.py` 启动

### 2. vcan0 接口不存在

**症状**:
```
Cannot find device "vcan0"
```

**解决方案**:
```bash
sudo modprobe vcan
sudo ip link add dev vcan0 type vcan
sudo ip link set up vcan0
```

### 3. master.dcf 找不到

**症状**:
```
Cannot open master config file
```

**解决方案**:
`master.dcf` 是编译时自动生成的，确保已运行 `colcon build`。

### 4. 控制器无法启动

**症状**:
```
waiting for service /controller_manager/list_controllers to become available...
```

**原因**: `ros2_control_node` 崩溃或未启动成功

**解决方案**: 检查前面的错误日志，通常是 Boot Timeout 问题

## 🔍 调试技巧

### 监控 CAN 总线

```bash
# 实时查看 CAN 消息
candump -ta vcan0
```

### 查看 ROS2 节点状态

```bash
# 列出所有节点
ros2 node list

# 查看话题
ros2 topic list

# 查看控制器状态
ros2 control list_controllers
```

### 手动初始化关节 (通常不需要)

> **注意**: 使用 `moveit_ros2canopen_with_fake_slaves.launch.py` 启动时，关节会**自动初始化**，无需手动调用。

以下命令仅在特殊情况下使用（如调试、驱动器故障恢复、或使用独立 CANopen 启动方式时）：

```bash
# CIA 402 初始化服务 - 将驱动器从 "Switch On Disabled" 状态转换到 "Operation Enabled" 状态
ros2 service call /joint_1/init std_srvs/srv/Trigger
ros2 service call /joint_2/init std_srvs/srv/Trigger
ros2 service call /joint_3/init std_srvs/srv/Trigger
ros2 service call /joint_4/init std_srvs/srv/Trigger
ros2 service call /joint_5/init std_srvs/srv/Trigger
ros2 service call /joint_6/init std_srvs/srv/Trigger
```

**CIA 402 状态机说明**:
- `Switch On Disabled` → (init) → `Operation Enabled`
- 只有在 `Operation Enabled` 状态下，驱动器才能接收运动指令




