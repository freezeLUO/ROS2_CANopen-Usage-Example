"""
无头模式 (Headless) 的 CANopen + MoveIt2 launch 文件
不启动 RViz，适合用于：
- 命令行测试
- Python 脚本控制
- CI/CD 自动化测试
- 服务器端部署

使用方法:
1. 启动系统:
   ros2 launch prbt_robot_moveit_config moveit_ros2canopen_headless.launch.py

2. 测试规划执行 (另开终端):
   # 查看当前关节状态
   ros2 topic echo /joint_states --once
   
   # 使用 moveit_py 或 Python API 进行规划
   # 或者使用 ros2 action 发送轨迹
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch.launch_description_sources import PythonLaunchDescriptionSource
from moveit_configs_utils import MoveItConfigsBuilder

import os
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    def with_sequential_delay(actions, step_seconds=5.0):
        """Wrap each action with a TimerAction spaced step_seconds apart."""
        delayed_actions = []
        cumulative_delay = 0.0
        for action in actions:
            delayed_actions.append(
                TimerAction(
                    period=cumulative_delay,
                    actions=[action],
                )
            )
            cumulative_delay += step_seconds
        return delayed_actions

    # 可选参数：是否使用仿真时间
    use_sim_time_arg = DeclareLaunchArgument(
        "use_sim_time",
        default_value="false",
        description="Use simulation time",
    )

    moveit_config = (
        MoveItConfigsBuilder("prbt_robot")
        .robot_description(
            file_path="config/prbt_canopen.urdf.xacro",
        )
        .robot_description_semantic(file_path="config/prbt.srdf")
        .planning_scene_monitor(
            publish_robot_description=True, publish_robot_description_semantic=True
        )
        .trajectory_execution(file_path="config/moveit_controllers.yaml")
        .to_moveit_configs()
    )

    # Start the actual move_group node/action server
    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[moveit_config.to_dict()],
        arguments=["--ros-args", "--log-level", "info"],
    )

    # Static TF
    static_tf_node = Node(
        package="tf2_ros",
        executable="static_transform_publisher",
        name="static_transform_publisher",
        output="log",
        arguments=["0.0", "0.0", "0.0", "0.0", "0.0", "0.0", "world", "base_link"],
    )

    # Publish TF
    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="both",
        parameters=[moveit_config.robot_description],
    )

    # ros2_control using CANopen hardware
    ros2_controllers_path = os.path.join(
        get_package_share_directory("prbt_robot_moveit_config"),
        "config",
        "prbt_canopen_ros2_controllers.yaml",
    )
    ros2_control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[ros2_controllers_path],
        remappings=[
            ("/controller_manager/robot_description", "/robot_description"),
        ],
        output="screen",
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
        ],
    )

    prbt_group_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["prbt_group_controller", "-c", "/controller_manager"],
    )

    # Include fake_slaves launch file - START THIS FIRST!
    fake_slaves_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("prbt_robot_support"),
                "launch",
                "fake_slaves.launch.py"
            ])
        ])
    )

    sequenced_actions = with_sequential_delay(
        [
            fake_slaves_launch,
            use_sim_time_arg,
            static_tf_node,
            robot_state_publisher,
            move_group_node,
            ros2_control_node,
            joint_state_broadcaster_spawner,
            prbt_group_controller_spawner,
        ]
    )

    return LaunchDescription(sequenced_actions)
