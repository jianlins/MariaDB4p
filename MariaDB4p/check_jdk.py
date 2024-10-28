import jdk
import sys
import subprocess
import os
from pathlib import Path
from loguru import logger
def is_jdk_installed():
    """
    Check if JDK is installed by attempting to run 'java -version'.
    """
    current_dir=Path(__file__).parent    
    logger.debug(f'current_dir:{current_dir}')
    if is_jdk_inpath():
        return 'java'
    elif 'JAVA_HOME'  in os.environ and len(os.environ['JAVA_HOME'])>0:
        logger.info(f"jdk has been installed to:{os.environ['JAVA_HOME']}")
        if not Path(current_dir, 'path.config').exists():
            java_exe=str(Path(os.environ['JAVA_HOME'],'bin','java'))
            Path(current_dir, 'path.config').write_text(java_exe)
        return str(Path(os.environ['JAVA_HOME'], 'bin','java'))
    elif Path(current_dir, 'path.config').exists():
        java_exe=Path(Path(current_dir,'path.config').read_text().strip())
        path_config=java_exe.parent.parent
        if path_config.exists():                         
            logger.info(f'jdk has been installed to: {str(path_config)}')
            os.environ['JAVA_HOME']=str(path_config)
            return java_exe

    logger.info("JDK is not installed.")
    return False
    
def is_jdk_inpath():
    try:
        result = subprocess.run(['java', '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("JDK is already installed.")
            return True        
    except FileNotFoundError:
        logger.info("JDK has not been found in system path.")
        return False


def install_jdk_if_missing():
    """
    Install JDK using the 'install-jdk' package if it's not already installed.
    """
    install_dir=''
    current_dir=Path(__file__).parent
    if not is_jdk_installed():
        logger.info("Installing JDK...")
        try:
            # Install JDK 17 from Adoptium
            install_dir=jdk.install('17', vendor='adoptium', path=str(Path.home() / '.jdks'))
            logger.info(f"JDK installed successfully to {install_dir}.")
            logger.info('No environmental variables have been configured. To uninstall, you can simply remove the directory.')
            Path(current_dir, 'path.config').write_text(str(Path(install_dir,'bin','java')))
        except Exception as e:
            logger.error(f"Failed to install JDK: {install_dir}")
            sys.exit(1)
    else:
        logger.info("Skipping JDK installation.")
    return install_dir



