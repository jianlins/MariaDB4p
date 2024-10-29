# MariaDB4p 
[![auto_ci](https://github.com/jianlins/MariaDB4p/actions/workflows/auto_ci.yml/badge.svg)](https://github.com/jianlins/MariaDB4p/actions/workflows/auto_ci.yml)

A python wrapper for [MariaDB4j](https://github.com/MariaDB4j/MariaDB4j)

MariaDB4j is a Java (!) "launcher" for MariaDB (the "backward compatible, drop-in replacement of the MySQL® Database Server", see Wikipedia), allowing you to use MariaDB (MySQL®) from Java without ANY installation / external dependencies. Read again: You do NOT have to have MariaDB binaries installed on your system to use MariaDB4j!


```python
from MariaDB4p.mariadb_wrapper import MariaDBWrapper
wrapper = MariaDBWrapper(port=3307)
wrapper.start_server()
wrapper.db.createDB('db')
# ---do something---
wrapper.stop_server()

```
For a demo notebook, check [here](https://github.com/jianlins/MariaDB4p/blob/main/notebooks/demo_mariadb.ipynb)