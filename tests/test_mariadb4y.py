from pathlib import Path
import time
from MariaDB4p.download_jars import download_maria4j_jars, DEPENDENCIES_DIR
from MariaDB4p.mariadb_wrapper import MariaDBWrapper
from loguru import logger
import shutil
def test_download_maria4j_jars():
    # Test case 1: Downloading the Maria4j JAR files
    assert download_maria4j_jars()
    jarfiles=list(Path(DEPENDENCIES_DIR).glob('*.jar'))
    print(jarfiles)
    assert len(jarfiles) > 0

def test_start_server():
    # Test case 2: Starting the MariaDB server
    wrapper = MariaDBWrapper(jdk_install_dir='.jdk')
    wrapper.start_server()
    time.sleep(5)
    assert (wrapper.db is not None)
    wrapper.db.createDB('test_db')
    logger.info("MariaDB server is running")    
    wrapper.stop_server()
    time.sleep(5)    
    shutil.rmtree(wrapper.base_dir)