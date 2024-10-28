import time
from MariaDB4p.download_jars import download_maria4j_jars
from MariaDB4p.mariadb_wrapper import MariaDBWrapper
from loguru import logger
import shutil
def test_download_maria4j_jars():
    # Test case 1: Downloading the Maria4j JAR files
    assert download_maria4j_jars()

def test_start_server():
    # Test case 2: Starting the MariaDB server
    wrapper = MariaDBWrapper()
    wrapper.start_server()
    time.sleep(5)
    assert (wrapper.db is not None)
    wrapper.db.createDB('test_db')
    logger.info("MariaDB server is running")    
    wrapper.stop_server()
    time.sleep(5)    
    shutil.rmtree(wrapper.base_dir)