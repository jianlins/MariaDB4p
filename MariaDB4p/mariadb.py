import os
import sys
import time
from pathlib import Path

# Import the download_dependencies script
from download_jars import download_artifact, initial_dependencies

# Import the MariaDBWrapper
from mariadb_wrapper import MariaDBWrapper

def setup_and_start():
    # Ensure dependencies are downloaded
    for group_id, artifact_id, version in initial_dependencies:
        download_artifact(group_id, artifact_id, version)

    # Initialize the wrapper
    wrapper = MariaDBWrapper(port=3307)

    try:
        # Start the server
        print("Starting MariaDB server...")
        wrapper.start_server()
        print("MariaDB server started.")

        # Application logic here
        time.sleep(10)

    except Exception as e:
        print(f"An error occurred: {e}")

    finally:
        # Stop the server
        print("Stopping MariaDB server...")
        wrapper.stop_server()
        print("MariaDB server stopped.")

if __name__ == "__main__":
    setup_and_start()
