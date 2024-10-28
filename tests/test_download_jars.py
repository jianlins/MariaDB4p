from MariaDB4p.download_jars import download_maria4j_jars

def test_download_maria4j_jars():
    # Test case 1: Downloading the Maria4j JAR files
    assert download_maria4j_jars() == "All dependencies downloaded."


test_download_maria4j_jars()
