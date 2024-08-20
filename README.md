# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/EffectiveRange/mrhat-daemon/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                             |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|--------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| generated/\_\_init\_\_.py        |        1 |        0 |        0 |        0 |    100% |           |
| generated/definitions.py         |       32 |        0 |        0 |        0 |    100% |           |
| generator/\_\_init\_\_.py        |        5 |        0 |        0 |        0 |    100% |           |
| generator/buildConfigLoader.py   |       19 |        0 |        4 |        0 |    100% |           |
| generator/codeFormatter.py       |       10 |        0 |        0 |        0 |    100% |           |
| generator/definitionConverter.py |       35 |        0 |        8 |        2 |     95% |52->55, 59->63 |
| generator/definitionGenerator.py |       32 |        0 |        0 |        0 |    100% |           |
| mrhat\_daemon/\_\_init\_\_.py    |        8 |        0 |        0 |        0 |    100% |           |
| mrhat\_daemon/appConfigLoader.py |       27 |        0 |        4 |        0 |    100% |           |
| mrhat\_daemon/i2cControl.py      |       81 |        0 |       14 |        3 |     97% |67->exit, 77->exit, 94->104 |
| mrhat\_daemon/mrHatControl.py    |       79 |        3 |        6 |        0 |     96% |   112-116 |
| mrhat\_daemon/mrHatDaemon.py     |       14 |        0 |        0 |        0 |    100% |           |
| mrhat\_daemon/piGpio.py          |       97 |        0 |       30 |        7 |     94% |72->exit, 99->102, 102->exit, 107->110, 115->118, 136->exit, 155->exit |
| mrhat\_daemon/picProgrammer.py   |      125 |        0 |       30 |        2 |     99% |90->93, 179->178 |
|                        **TOTAL** |  **565** |    **3** |   **96** |   **14** | **97%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/EffectiveRange/mrhat-daemon/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/EffectiveRange/mrhat-daemon/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/EffectiveRange/mrhat-daemon/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/EffectiveRange/mrhat-daemon/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2FEffectiveRange%2Fmrhat-daemon%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/EffectiveRange/mrhat-daemon/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.