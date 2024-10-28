import jpype
import jpype.imports
from jpype.types import *
import os
import sys
import time
from pathlib import Path
import pymysql
from loguru import logger

from MariaDB4p.download_jars import download_maria4j_jars
from MariaDB4p.check_jdk import install_jdk_if_missing, is_jdk_installed

class MariaDBWrapper:
    def __init__(self, port=3306, base_dir=None, jars_dir=Path(__file__).parent.parent / 'mariadb4j_jars', jdk_version=17):
        """
        Initialize the MariaDBWrapper.

        :param port: Port number for MariaDB to listen on.
        :param base_dir: Base directory for MariaDB data. If not provided, a temporary directory is used.
        """
        self.port = port
        install_jdk_if_missing(target_version=jdk_version)
        download_maria4j_jars()
        if base_dir is None:
            tmp_base=Path(Path.home(), 'mariadb4j_data')
            tmp_base.mkdir(exist_ok=True,parents=True)
            self.base_dir = str(tmp_base.resolve().absolute())
        else:
            self.base_dir = base_dir
        self.db = None

        # Initialize JPype
        if not jpype.isJVMStarted():
            self.start_jvm(jars_dir)

    def restart_jvm(self):
        self.stop_jvm()
        self.start_jvm()
       

    def start_jvm(self, jars_dir=Path(__file__).parent.parent / 'mariadb4j_jars'):
        """
        Start the JVM with the required classpath.
        """
        # Path to all JAR files in the mariadb4j_jars directory
        if not is_jdk_installed():
            logger.error("JDK is not installed. Please install JDK to use MariaDB4j.")
            sys.exit(1)   
        
        jars_dir=str(jars_dir)
        logger.info(f"Starting JVM with classpath: {jars_dir}/*")
        try:
            jpype.startJVM(classpath=[f'{jars_dir}/*'])
            logger.info("JVM started successfully.")
        except Exception as e:
            logger.error(f"Failed to start JVM: {e}")
            sys.exit(1)

    def start_server(self):
        """
        Start the embedded MariaDB server.
        """
        from ch.vorburger.mariadb4j import DBConfigurationBuilder
        from ch.vorburger.mariadb4j import DB

        # Configure the MariaDB server
        config_builder = DBConfigurationBuilder.newBuilder()
        if self.port:
            config_builder.setPort(self.port)
        if self.base_dir:
            config_builder.setDataDir(self.base_dir)

        

        # Create and start the database
        try:
            self.db  = DB.newEmbeddedDB(config_builder.build())
            self.db.start()
            logger.info(f"MariaDB server started on port {self.port}.")
        except Exception as e:
            logger.error(f"Failed to start MariaDB server: {e}")
            sys.exit(1)
        return True

    def stop_server(self):
        """
        Stop the embedded MariaDB server.
        """
        if self.db:
            try:
                self.db.stop()
                logger.info("MariaDB server stopped.")
                self.db = None
            except Exception as e:
                logger.error(f"Failed to stop MariaDB server: {e}")

    def is_running(self):
        """
        Check if the MariaDB server is running.

        :return: True if running, False otherwise.
        """
        if self.db:
            return self.db.isRunning()
        return False

    def create_database(self, db_name):
        """
        Create a new database.

        :param db_name: Name of the database to create.
        """
        if not self.db:
            raise Exception("MariaDB server is not running.")
        try:
            self.db.createDB(db_name)
            logger.info(f"Database '{db_name}' created.")
        except Exception as e:
            logger.error(f"Failed to create database '{db_name}': {e}")

    def create_user(self, user, password, host='localhost'):
        """
        Create a new user with all privileges.

        :param user: Username.
        :param password: Password for the user.
        :param host: Host for the user (default: 'localhost').
        """
        if not self.db:
            raise Exception("MariaDB server is not running.")
        try:
            self.db.run("mysql", "mysql", None, [
                "-e",
                f"CREATE USER '{user}'@'{host}' IDENTIFIED BY '{password}';"
            ])
            self.db.run("mysql", "mysql", None, [
                "-e",
                f"GRANT ALL PRIVILEGES ON *.* TO '{user}'@'{host}' WITH GRANT OPTION;"
            ])
            self.db.run("mysql", "mysql", None, ["-e", "FLUSH PRIVILEGES;"])
            logger.info(f"User '{user}'@'{host}' created with all privileges.")
        except Exception as e:
            logger.error(f"Failed to create user '{user}'@'{host}': {e}")

    def execute_query(self, query, db_name='testdb', user='root', password=''):
        """
        Execute an SQL query on the specified database.

        :param query: SQL query to execute.
        :param db_name: Database name.
        :param user: Username for authentication.
        :param password: Password for authentication.
        """
        connection = pymysql.connect(
            host='localhost',
            port=self.port,
            user=user,
            password=password,
            database=db_name
        )
        try:
            with connection.cursor() as cursor:
                cursor.execute(query)
                connection.commit()
                logger.info(f"Executed query: {query}")
        except Exception as e:
            logger.error(f"Failed to execute query '{query}': {e}")
        finally:
            connection.close()

    def __del__(self):
        """
        Destructor to ensure the MariaDB server is stopped and JVM is shutdown.
        """
        self.stop_server()
        if jpype.isJVMStarted():
            jpype.shutdownJVM()
            logger.info("JVM shutdown.")