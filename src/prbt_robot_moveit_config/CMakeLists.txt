cmake_minimum_required(VERSION 3.22)
project(prbt_robot_moveit_config)

find_package(ament_cmake REQUIRED)

ament_package()

if(EXISTS "${CMAKE_CURRENT_SOURCE_DIR}/launch")
  install(
    DIRECTORY launch
    DESTINATION share/${PROJECT_NAME}
    PATTERN "setup_assistant.launch" EXCLUDE)
endif()

install(DIRECTORY config DESTINATION share/${PROJECT_NAME})
install(FILES .setup_assistant DESTINATION share/${PROJECT_NAME})

install(PROGRAMS
  scripts/home_to_pose1.py
  scripts/test_moveit_headless.py
  DESTINATION lib/${PROJECT_NAME}
)
