#!/usr/bin/env python3
"""
MoveIt2 无头模式测试脚本
用于测试 moveit_ros2canopen_headless.launch.py 是否正常工作

使用方法:
1. 先启动无头模式:
   ros2 launch prbt_robot_moveit_config moveit_ros2canopen_headless.launch.py

2. 运行此脚本:
   ros2 run prbt_robot_moveit_config test_moveit_headless.py
   或
   python3 test_moveit_headless.py
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import (
    MotionPlanRequest,
    PlanningOptions,
    Constraints,
    JointConstraint,
    RobotState,
)
from sensor_msgs.msg import JointState
from std_msgs.msg import Header
import sys


class MoveItHeadlessTest(Node):
    def __init__(self):
        super().__init__("moveit_headless_test")
        
        # Action client for MoveGroup
        self._action_client = ActionClient(self, MoveGroup, "move_action")
        
        # Subscribe to joint states
        self._joint_states = None
        self._joint_sub = self.create_subscription(
            JointState, "/joint_states", self._joint_states_callback, 10
        )
        
        self.get_logger().info("MoveIt2 Headless Test Node initialized")
        self.get_logger().info("Waiting for MoveGroup action server...")
        
    def _joint_states_callback(self, msg):
        self._joint_states = msg
        
    def wait_for_server(self, timeout_sec=30.0):
        """等待 MoveGroup action server"""
        return self._action_client.wait_for_server(timeout_sec=timeout_sec)
    
    def get_current_joint_values(self):
        """获取当前关节值"""
        if self._joint_states is None:
            return None
        return dict(zip(self._joint_states.name, self._joint_states.position))
    
    def plan_to_joint_goal(self, joint_goals: dict, planning_group: str = "prbt_group"):
        """
        规划到指定关节位置
        
        Args:
            joint_goals: 关节目标字典 {"joint_1": 0.5, "joint_2": -0.3, ...}
            planning_group: 规划组名称
        """
        goal_msg = MoveGroup.Goal()
        
        # 设置规划请求
        goal_msg.request = MotionPlanRequest()
        goal_msg.request.group_name = planning_group
        goal_msg.request.num_planning_attempts = 10
        goal_msg.request.allowed_planning_time = 5.0
        goal_msg.request.max_velocity_scaling_factor = 0.5
        goal_msg.request.max_acceleration_scaling_factor = 0.5
        
        # 设置目标约束
        goal_constraints = Constraints()
        for joint_name, joint_value in joint_goals.items():
            jc = JointConstraint()
            jc.joint_name = joint_name
            jc.position = joint_value
            jc.tolerance_above = 0.01
            jc.tolerance_below = 0.01
            jc.weight = 1.0
            goal_constraints.joint_constraints.append(jc)
        
        goal_msg.request.goal_constraints.append(goal_constraints)
        
        # 设置规划选项
        goal_msg.planning_options = PlanningOptions()
        goal_msg.planning_options.plan_only = False  # False = 规划并执行
        goal_msg.planning_options.look_around = False
        goal_msg.planning_options.replan = True
        goal_msg.planning_options.replan_attempts = 3
        
        self.get_logger().info(f"Sending goal: {joint_goals}")
        
        # 发送目标
        send_goal_future = self._action_client.send_goal_async(
            goal_msg, feedback_callback=self._feedback_callback
        )
        send_goal_future.add_done_callback(self._goal_response_callback)
        
        return send_goal_future
    
    def _goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("Goal rejected!")
            return
        
        self.get_logger().info("Goal accepted, waiting for result...")
        result_future = goal_handle.get_result_async()
        result_future.add_done_callback(self._get_result_callback)
    
    def _get_result_callback(self, future):
        result = future.result().result
        if result.error_code.val == 1:  # SUCCESS
            self.get_logger().info("Motion executed successfully!")
        else:
            self.get_logger().error(f"Motion failed with error code: {result.error_code.val}")
    
    def _feedback_callback(self, feedback_msg):
        feedback = feedback_msg.feedback
        self.get_logger().info(f"State: {feedback.state}")


def main(args=None):
    rclpy.init(args=args)
    node = MoveItHeadlessTest()
    
    # 等待 action server
    if not node.wait_for_server(timeout_sec=30.0):
        node.get_logger().error("MoveGroup action server not available!")
        node.destroy_node()
        rclpy.shutdown()
        return
    
    node.get_logger().info("MoveGroup action server is available!")
    
    # 等待接收关节状态
    node.get_logger().info("Waiting for joint states...")
    while rclpy.ok() and node._joint_states is None:
        rclpy.spin_once(node, timeout_sec=0.5)
    
    current_joints = node.get_current_joint_values()
    node.get_logger().info(f"Current joint values: {current_joints}")
    
    # 定义测试目标位置 (小幅度移动)
    test_goal = {
        "joint_1": 0.2,
        "joint_2": -0.2,
        "joint_3": 0.2,
        "joint_4": -0.2,
    }
    
    node.get_logger().info("=" * 50)
    node.get_logger().info("Starting motion planning test...")
    node.get_logger().info(f"Target: {test_goal}")
    node.get_logger().info("=" * 50)
    
    # 发送规划请求
    node.plan_to_joint_goal(test_goal)
    
    # 运行直到完成
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
