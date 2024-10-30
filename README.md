# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/EffectiveRange/mrhat-daemon/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                             |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|--------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| generated/\_\_init\_\_.py        |        1 |        0 |        0 |        0 |    100% |           |
| generated/definitions.py         |       32 |        0 |        0 |        0 |    100% |           |
| generator/\_\_init\_\_.py        |        5 |        0 |        0 |        0 |    100% |           |
| generator/buildConfigLoader.py   |       19 |        0 |        4 |        0 |    100% |           |
| generator/codeFormatter.py       |       10 |        0 |        0 |        0 |    100% |           |
| generator/definitionConverter.py |       35 |        0 |        6 |        1 |     98% |    59->63 |
| generator/definitionGenerator.py |       32 |        0 |        0 |        0 |    100% |           |
| mrhat\_daemon/\_\_init\_\_.py    |        8 |        0 |        0 |        0 |    100% |           |
| mrhat\_daemon/apiServer.py       |      121 |        5 |       14 |        0 |     96% |60-62, 68-69 |
| mrhat\_daemon/appConfigLoader.py |       27 |        0 |        4 |        0 |    100% |           |
| mrhat\_daemon/i2cControl.py      |       92 |        0 |       14 |        2 |     98% |88->exit, 104->exit |
| mrhat\_daemon/mrHatControl.py    |      125 |        0 |       10 |        0 |    100% |           |
| mrhat\_daemon/mrHatDaemon.py     |       14 |        0 |        0 |        0 |    100% |           |
| mrhat\_daemon/piGpio.py          |      109 |        0 |       30 |        7 |     95% |104->107, 107->exit, 112->115, 120->123, 132->exit, 152->exit, 171->exit |
| mrhat\_daemon/picProgrammer.py   |      125 |        0 |       26 |        2 |     99% |90->93, 179->178 |
|                        **TOTAL** |  **755** |    **5** |  **108** |   **12** | **98%** |           |


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