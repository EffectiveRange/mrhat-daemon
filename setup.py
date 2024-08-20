from os.path import dirname, abspath

from setuptools import setup, find_packages
from setuptools.command.build_py import build_py


class GenerateDefinitionsAndBuild(build_py):

    def run(self):
        try:
            self._generate_definitions()
        except ModuleNotFoundError:
            print('Skip generating definitions')

        super().run()

    def _generate_definitions(self):
        from context_logger import setup_logging
        from generator import GeneratorApp

        setup_logging('mrhat-daemon-generator')

        project_root = abspath(dirname(__file__))

        generator_app = GeneratorApp(project_root)

        generator_app.run()

        self.distribution.packages.append('generated')


setup(
    name='mrhat-daemon',
    version='0.1.0',
    description='MrHat supervisor background service',
    long_description='MrHat supervisor background service',
    author='Ferenc Nandor Janky & Attila Gombos',
    author_email='info@effective-range.com',
    maintainer='Ferenc Nandor Janky & Attila Gombos',
    maintainer_email='info@effective-range.com',
    packages=find_packages(exclude=['tests']),
    scripts=['bin/mrhat-daemon.py'],
    data_files=[('config', ['config/mrhat-daemon.conf'])],
    setup_requires=[
        'black',
        'python-context-logger@git+https://github.com/EffectiveRange/python-context-logger.git@latest',
        'python-common-utility@git+https://github.com/EffectiveRange/python-common-utility.git@latest',
    ],
    install_requires=[
        'black',
        'packaging',
        'flask',
        'waitress',
        'pigpio',
        'dbus-python',
        'python-context-logger@git+https://github.com/EffectiveRange/python-context-logger.git@latest',
        'python-common-utility@git+https://github.com/EffectiveRange/python-common-utility.git@latest',
        'python-systemd-dbus@git+https://github.com/EffectiveRange/python-systemd-dbus.git@latest',
    ],
    cmdclass={'build_py': GenerateDefinitionsAndBuild},
)
