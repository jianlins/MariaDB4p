import jdk
import sys
import subprocess
import os
from pathlib import Path
from loguru import logger
import traceback
def get_jdk_version(executable='java'):
    """
    Returns the installed JDK version or None if JDK is not installed.
    """
    try:
        result = subprocess.run([executable, '-version'], capture_output=True, text=True)
        if result.returncode == 0:
            version_line = result.stderr.split('\n')[0]  # Typically, version info is in stderr
            version = int(version_line.split()[2].strip('"').split('.')[0])
            logger.info(f"Installed JDK version: {version}")
            return version
        else:
            logger.info("Failed to determine JDK version.")
            return 0
    except FileNotFoundError:
        logger.info("JDK is not installed.")
        return 0

def is_jdk_installed(target_version=17):
    """
    Check if JDK is installed by attempting to run 'java -version'.
    """
    current_dir=Path(__file__).parent    
    logger.debug(f'current_dir:{current_dir}')
    if get_jdk_version()==target_version:
        return 'java'
    elif 'JAVA_HOME'  in os.environ and len(os.environ['JAVA_HOME'])>0:
        logger.info(f"jdk has been installed to:{os.environ['JAVA_HOME']}")
        if not Path(current_dir, 'path.config').exists():
            java_exe=str(Path(os.environ['JAVA_HOME'],'bin','java'))
            if get_jdk_version(java_exe)==target_version:
                Path(current_dir, 'path.config').write_text(java_exe)
                return str(Path(os.environ['JAVA_HOME'], 'bin','java'))
    elif Path(current_dir, 'path.config').exists():
        java_exe=Path(Path(current_dir,'path.config').read_text().strip())
        path_config=java_exe.parent.parent
        if path_config.exists() and get_jdk_version(java_exe)==target_version:
            logger.info(f'jdk has been installed to: {str(path_config)}')
            os.environ['JAVA_HOME']=str(path_config)
            return java_exe

    logger.info(f"JDK{target_version} is not installed.")
    return None
    


def install_jdk_if_missing(target_version=17):
    """
    Install JDK using the 'install-jdk' package if it's not already installed.
    """
    install_dir=''
    current_dir=Path(__file__).parent
    if is_jdk_installed(target_version) is None:
        logger.info(f"Installing JDK {target_version}...")
        try:
            # Install JDK 17 from Adoptium
            install_dir=jdk.install('17', vendor='adoptium', path=str(Path.home() / '.jdks'))
            logger.info(f"JDK installed successfully to {install_dir}.")
            logger.info('No environmental variables have been configured. To uninstall, you can simply remove the directory.')
            Path(current_dir, 'path.config').write_text(str(Path(install_dir,'bin','java')))
        except Exception as e:
            tb_str = traceback.format_exc()
            logger.error(f"Failed to install JDK: {install_dir}\n {str(e)}\nTraceback:\n{tb_str}")            
            sys.exit(1)
    else:
        logger.info("Skipping JDK installation.")
    return install_dir



