# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

from subprocess import CompletedProcess, run, PIPE, Popen

from context_logger import get_logger

log = get_logger('PlatformAccess')


class IPlatformAccess(object):

    def execute_command(self, command: list[str]) -> CompletedProcess[str]:
        raise NotImplementedError()

    def execute_command_async(self, command: list[str]) -> None:
        raise NotImplementedError()


class PlatformAccess(IPlatformAccess):

    def execute_command(self, command: list[str]) -> CompletedProcess[str]:
        log.info('Executing command', command=command)

        result = run(command, stdout=PIPE, stderr=PIPE, text=True)

        if result.returncode != 0:
            log.error('Command failed', returncode=result.returncode, stderr=result.stderr)
        else:
            log.info('Command executed successfully')

        return result

    def execute_command_async(self, command: list[str]) -> None:
        log.info('Executing command asynchronously', command=command)

        Popen(command, stdout=PIPE, stderr=PIPE, text=True)
