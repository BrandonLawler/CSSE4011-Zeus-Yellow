# SPDX-License-Identifier: Apache-2.0
#Setting to exclusively build for the Thingy
set(BOARD thingy52_nrf52832)
set(BOARD_FLASH_RUNNER jlink)
#set(DTC_OVERLAY_FILE boards/mpu9250.overlay)
set(CONF_FILE prj.conf rtt_console.conf bt.conf)

cmake_minimum_required(VERSION 3.13.1)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(mobile)

#Add include_directories for libraries, path starts from this files location.
include_directories(inc/
                    lib/)

target_sources(app PRIVATE src/main.c
                           src/mobile_node_ble.c
                           src/mobile_connect.c
                           #src/hal_mpu9250.c
                           src/hal_imu.c
                           lib/zephyr_i2c.c
                           lib/inv_mpu.c
                           lib/inv_mpu_dmp_motion_driver.c
                           )
