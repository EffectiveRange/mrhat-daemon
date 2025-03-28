#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

import os
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, BooleanOptionalAction
from pathlib import Path
from signal import signal, SIGINT, SIGTERM
from typing import Any

from common_utility import SessionProvider, FileDownloader, ConfigLoader
from context_logger import setup_logging, get_logger
from dbus import SystemBus
from systemd_dbus import SystemdDbus

from mrhat_daemon import (
    MrHatDaemon,
    ApiServer,
    I2CControl,
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
    ApiServerConfiguration,
    MrHatControlConfig,
)

APPLICATION_NAME = 'mrhat-daemon'

log = get_logger('MrHatDaemonApp')


def main() -> None:
    resource_root = _get_resource_root()
    arguments = _get_arguments()

    setup_logging(APPLICATION_NAME)

    log.info(f'Started {APPLICATION_NAME}', arguments=arguments)

    config = ConfigLoader(resource_root, f'config/{APPLICATION_NAME}.conf').load(arguments)

    _update_logging(config)

    log.info('Retrieved configuration', configuration=config)

    try:
        api_server_port = int(config['api_server_port'])
        power_off_forced = bool(config['power_off_forced'])
        systemd_retry_limit = int(config['systemd_retry_limit'])
        systemd_retry_delay = float(config['systemd_retry_delay'])
        firmware_package_dir = config['firmware_package_dir']
        firmware_package_file = config['firmware_package_file']
        firmware_auto_upgrade = bool(config['firmware_auto_upgrade'])
        interrupt_pin = int(config['interrupt_pin'])
        interrupt_pull = GpioPullType[config['interrupt_pull']]
        interrupt_edge = GpioEdgeType[config['interrupt_edge']]
        i2c_bus_id = int(config['i2c_bus_id'])
        i2c_address = int(config['i2c_address'], 16)
        i2c_retry_limit = int(config['i2c_retry_limit'])
        i2c_retry_delay = float(config['i2c_retry_delay'])
    except KeyError as error:
        raise ValueError(f'Missing configuration key: {error}')

    platform_access = PlatformAccess()
    session_provider = SessionProvider()
    file_downloader = FileDownloader(session_provider, firmware_package_dir)

    systemd = SystemdDbus(SystemBus())

    service_config = ServiceConfig(systemd_retry_limit, systemd_retry_delay)
    interrupt_config = InterruptConfig(interrupt_pin, interrupt_pull, interrupt_edge)

    with PiGpio(systemd, platform_access, service_config, interrupt_config) as pi_gpio:
        gpio_options = {gpio: int(pin) for gpio, pin in config.items() if gpio.startswith('gpio')}
        programmer_config = ProgrammerConfig(gpio_options, firmware_package_dir, firmware_package_file)
        i2c_config = I2CConfig(i2c_bus_id, i2c_address, i2c_retry_limit, i2c_retry_delay)
        control_config = MrHatControlConfig(firmware_auto_upgrade, power_off_forced)
        api_server_config = ApiServerConfiguration(api_server_port, resource_root)

        with (
            PicProgrammer(programmer_config, platform_access, file_downloader) as pic_programmer,
            I2CControl(pi_gpio, i2c_config) as i2c_control,
            MrHatControl(pi_gpio, pic_programmer, i2c_control, platform_access, control_config) as mr_hat_control,
            ApiServer(api_server_config, mr_hat_control) as api_server,
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
        '-c',
        '--config-file',
        help='configuration file',
        default=f'/etc/effective-range/{APPLICATION_NAME}/{APPLICATION_NAME}.conf',
    )

    parser.add_argument('-f', '--log-file', help='log file path')
    parser.add_argument('-l', '--log-level', help='logging level')

    parser.add_argument('--api-server-port', help='web server port to listen on', type=int)

    parser.add_argument('--power-off-forced', help='force power off the system', action=BooleanOptionalAction)

    parser.add_argument('--systemd-retry-limit', help='systemd operation retry limit', type=int)
    parser.add_argument('--systemd-retry-delay', help='systemd operation retry delay', type=float)

    parser.add_argument('--firmware-package-dir', help='MrHat firmware directory path')
    parser.add_argument('--firmware-package-file', help='MrHat firmware file path or URL')
    parser.add_argument('--firmware-auto-upgrade', help='automatically upgrade firmware', action=BooleanOptionalAction)

    parser.add_argument('--interrupt-pin', help='interrupt GPIO pin number of the device', type=int)
    parser.add_argument('--interrupt-pull', help='interrupt GPIO pin PULL_UP or PULL_DOWN')
    parser.add_argument('--interrupt-edge', help='interrupt GPIO pin FALLING_EDGE or RISING_EDGE')

    parser.add_argument('--i2c-bus-id', help='I2C bus ID of the device', type=int)
    parser.add_argument('--i2c-address', help='I2C address of the device', type=int)
    parser.add_argument('--i2c-retry-limit', help='I2C operation retry limit', type=int)
    parser.add_argument('--i2c-retry-delay', help='I2C operation retry delay', type=float)

    return {k: v for k, v in vars(parser.parse_args()).items() if v is not None}


def _get_resource_root() -> str:
    return str(Path(os.path.dirname(__file__)).parent.absolute())


def _update_logging(configuration: dict[str, Any]) -> None:
    log_level = configuration.get('log_level', 'INFO')
    log_file = configuration.get('log_file')
    setup_logging(APPLICATION_NAME, log_level, log_file, warn_on_overwrite=False)


if __name__ == '__main__':
    main()
