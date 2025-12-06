#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from moveit_py.core import RobotModel, RobotState
from moveit_py.planning import PlanningContext, PlanningSceneMonitor


class HomeToPose1Node(Node):
    def __init__(self):
        super().__init__("home_to_pose1_node")

        self.get_logger().info("Initializing moveit_py...")

        # 载入机器人模型
        robot_model = RobotModel("robot_description")

        # 监控规划场景（包含当前关节状态等）
        scene_monitor = PlanningSceneMonitor(robot_model, "planning_scene_monitor")
        scene_monitor.start_state_monitor("joint_states")

        # 等一小会儿让当前状态更新
        self.get_clock().sleep_for(rclpy.time.Duration(seconds=1.0))

        # 创建规划上下文：指定规划组
        group_name = "manipulator"  # 如与你的 SRDF 不符，可调整
        planning_context = PlanningContext(robot_model, group_name, scene_monitor)

        # 使用命名状态 "home" 作为起始状态（如果已在 SRDF 中配置）
        start_state = RobotState(robot_model)
        if start_state.set_to_default_values(group_name, "home"):
            self.get_logger().info("Start state set to named state 'home'")
        else:
            self.get_logger().warn("Named state 'home' not found, using current state")
            start_state = scene_monitor.current_state

        # 使用命名状态 "pose1" 作为目标状态（如果已在 SRDF 中配置）
        goal_state = RobotState(robot_model)
        if goal_state.set_to_default_values(group_name, "pose1"):
            self.get_logger().info("Goal state set to named state 'pose1'")
        else:
            self.get_logger().error("Named state 'pose1' not found, aborting")
            rclpy.shutdown()
            return

        # 设置规划问题
        planning_context.set_start_and_goal_states(start_state, goal_state)

        self.get_logger().info("Planning from 'home' to 'pose1'...")
        result = planning_context.plan()

        if not result or not result.trajectory:
            self.get_logger().error("Planning failed or returned empty trajectory")
        else:
            traj = result.trajectory
            jt = traj.joint_trajectory
            self.get_logger().info(f"Trajectory has {len(jt.points)} points")
            for i, p in enumerate(jt.points[:5]):  # 只打印前 5 个点
                t = p.time_from_start.sec + p.time_from_start.nanosec * 1e-9
                self.get_logger().info(
                    f"Point {i}: positions={list(p.positions)}, time_from_start={t:.3f}s"
                )

        # 只做规划和打印，不执行；任务完成后退出
        rclpy.shutdown()


def main(args=None):
    rclpy.init(args=args)
    node = HomeToPose1Node()
    rclpy.spin(node)


if __name__ == "__main__":
    main()
