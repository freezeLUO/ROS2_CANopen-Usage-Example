import os

from launch import LaunchDescription, events
from launch.actions import EmitEvent, LogInfo, RegisterEventHandler
from launch_ros.actions import LifecycleNode
from launch_ros.event_handlers import OnStateTransition
from launch_ros.events.lifecycle import ChangeState

import lifecycle_msgs.msg
from ament_index_python.packages import get_package_share_directory


def _create_slave_actions(node_name, node_id, config_path, can_interface):
    """Create lifecycle node, configure event, and activation handler for one slave."""
    slave_node = LifecycleNode(
        name=node_name,
        namespace="",
        package="canopen_fake_slaves",
        executable="cia402_slave_node",
        output="screen",
        parameters=[
            {
                "slave_config": config_path,
                "node_id": node_id,
                "can_interface_name": can_interface,
            }
        ],
    )

    configure_event = EmitEvent(
        event=ChangeState(
            lifecycle_node_matcher=events.matches_action(slave_node),
            transition_id=lifecycle_msgs.msg.Transition.TRANSITION_CONFIGURE,
        )
    )

    activation_handler = RegisterEventHandler(
        OnStateTransition(
            target_lifecycle_node=slave_node,
            goal_state="inactive",
            handle_once=True,
            entities=[
                LogInfo(msg=f"node '{node_name}' reached the 'inactive' state, activating."),
                EmitEvent(
                    event=ChangeState(
                        lifecycle_node_matcher=events.matches_action(slave_node),
                        transition_id=lifecycle_msgs.msg.Transition.TRANSITION_ACTIVATE,
                    )
                ),
            ],
        )
    )

    return slave_node, configure_event, activation_handler


def generate_launch_description():
    prbt_support_dir = get_package_share_directory("prbt_robot_support")
    slave_config_path = os.path.join(prbt_support_dir, "config", "prbt", "ZeroErr_Driver_V1.5.eds")
    can_interface = "vcan0"

    node_definitions = {
        "joint_1": 1,
        "joint_2": 2,
        "joint_3": 3,
        "joint_4": 4,
    }

    actions = []
    for node_name, node_id in node_definitions.items():
        slave_node, configure_event, activation_handler = _create_slave_actions(
            node_name,
            node_id,
            slave_config_path,
            can_interface,
        )
        actions.extend([slave_node, configure_event, activation_handler])

    return LaunchDescription(actions)