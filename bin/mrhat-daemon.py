#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

import os
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from pathlib import Path
from signal import signal, SIGINT, SIGTERM
from typing import Any

from common_utility import SessionProvider, FileDownloader
from context_logger import setup_logging, get_logger
from systemd_dbus import SystemdDbus

from mrhat_daemon import (
    MrHatDaemon,
    ApiServer,
    I2CControl,
    ConfigLoader,
    MrHatControl,
    PicProgrammer,
    PlatformAccess,
    PiGpio,
    ProgrammerConfig,
    I2CConfig,
    ServiceConfig,
    InterruptConfig,
    GpioPullType,
    GpioEdgeType,
)

APPLICATION_NAME = 'mrhat-daemon'

log = get_logger('MrHatDaemonApp')


def main() -> None:
    resource_root = _get_resource_root()
    arguments = _get_arguments()

    setup_logging(APPLICATION_NAME)

    config = ConfigLoader(resource_root).load(arguments)

    _update_logging(config)

    log.info(f'Started {APPLICATION_NAME}', arguments=config)

    platform_access = PlatformAccess()
    session_provider = SessionProvider()
    file_downloader = FileDownloader(session_provider, config.get('firmware_dir', '/tmp'))

    systemd = SystemdDbus()

    service_retry_limit = int(config.get('service_retry_limit', 5))
    service_retry_delay = float(config.get('service_retry_delay', 1))
    service_config = ServiceConfig(service_retry_limit, service_retry_delay)

    gpio_pin = int(config.get('interrupt_pin', 4))
    pull_type = GpioPullType[config.get('interrupt_pull', 'PULL_UP')]
    edge_type = GpioEdgeType[config.get('interrupt_edge', 'FALLING_EDGE')]
    interrupt_config = InterruptConfig(gpio_pin, pull_type, edge_type)

    with PiGpio(systemd, service_config, interrupt_config) as pi_gpio:
        firmware_dir = config.get('firmware_dir')
        firmware_file = config.get('firmware_file')
        gpio_options = {gpio: int(pin) for gpio, pin in config.items() if gpio.startswith('gpio')}
        programmer_config = ProgrammerConfig(firmware_dir, firmware_file, gpio_options)

        i2c_bus_id = int(config.get('i2c_bus_id', 1))
        i2c_address = int(config.get('i2c_address', '0x33'), 16)
        i2c_retry_limit = int(config.get('i2c_retry_limit', 3))
        i2c_retry_delay = float(config.get('i2c_retry_delay', 0.1))
        i2c_config = I2CConfig(i2c_bus_id, i2c_address, i2c_retry_limit, i2c_retry_delay)

        with (
            PicProgrammer(programmer_config, platform_access, file_downloader) as pic_programmer,
            I2CControl(pi_gpio, i2c_config) as i2c_control,
            MrHatControl(pi_gpio, pic_programmer, i2c_control, platform_access) as mr_hat_control,
            ApiServer(config.get('server_port', 9000)) as api_server,
        ):
            mr_hat_daemon = MrHatDaemon(mr_hat_control, api_server)

            def handler(signum: int, frame: Any) -> None:
                log.info(f'Shutting down {APPLICATION_NAME}', signum=signum)
                mr_hat_daemon.shutdown()
                return

            signal(SIGINT, handler)
            signal(SIGTERM, handler)

            mr_hat_daemon.run()


def _get_arguments() -> dict[str, Any]:
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-c', '--config-file', help='configuration file', default=f'/etc/{APPLICATION_NAME}/{APPLICATION_NAME}.conf'
    )
    parser.add_argument('--log-file', help='log file path')
    parser.add_argument('--log-level', help='logging level')
    parser.add_argument('-p', '--server-port', help='web server port to listen on', type=int)
    parser.add_argument('-b', '--i2c-bus-number', help='I2C bus number of the device', type=int)
    parser.add_argument('-a', '--i2c-address', help='I2C address of the device', type=int)
    parser.add_argument('-i', '--interrupt-pin', help='interrupt GPIO pin number of the device', type=int)
    parser.add_argument('-d', '--firmware-dir', help='MrHat firmware directory path')
    parser.add_argument('-f', '--firmware-file', help='MrHat firmware file path or URL')

    return {k: v for k, v in vars(parser.parse_args()).items() if v is not None}


def _get_resource_root() -> str:
    return str(Path(os.path.dirname(__file__)).parent.absolute())


def _update_logging(configuration: dict[str, Any]) -> None:
    log_level = configuration.get('log_level', 'INFO')
    log_file = configuration.get('log_file')
    setup_logging(APPLICATION_NAME, log_level, log_file, warn_on_overwrite=False)


if __name__ == '__main__':
    main()
