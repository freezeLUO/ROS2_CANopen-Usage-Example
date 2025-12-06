cmake_minimum_required(VERSION 3.5)

project(arm_prbt)

find_package(ament_cmake REQUIRED)

install(DIRECTORY
	config
	launch
	meshes
	urdf
	DESTINATION share/${PROJECT_NAME}
)

ament_package()
