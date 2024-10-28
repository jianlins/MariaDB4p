import os
import urllib.request
from pathlib import Path
import xml.etree.ElementTree as ET
from urllib.parse import quote
import re
from loguru import logger

# Directory to store downloaded JARs
mariadb4y_root=Path(__file__).parent.parent
DEPENDENCIES_DIR = Path(mariadb4y_root, "mariadb4j_jars")


# Maven Central Base URL
MAVEN_CENTRAL = "https://repo1.maven.org/maven2/"

# Function to construct the Maven Central URL for a given artifact
def construct_maven_url(group_id, artifact_id, version, file_type="jar"):
    group_path = group_id.replace('.', '/')
    artifact_path = f"{group_path}/{artifact_id}/{version}/{artifact_id}-{version}.{file_type}"
    return MAVEN_CENTRAL + artifact_path

# Function to download a file from a URL
def download_file(url, dest):
    if dest.exists():
        logger.info(f"Already downloaded: {dest}")
        return True
    logger.info(f"Downloading {url} to {dest}...")
    try:
        urllib.request.urlretrieve(url, dest)
        logger.info(f"Downloaded: {dest}")
        return True
    except Exception as e:
        logger.warning(f"Failed to download {url}")
    return False

# Function to resolve properties in text
def resolve_properties(text, properties):
    if text is None:
        return None
    pattern = re.compile(r'\$\{([^}]+)\}')
    while True:
        match = pattern.search(text)
        if not match:
            break
        prop_name = match.group(1)
        prop_value = properties.get(prop_name)
        if prop_value is None:
            # Cannot resolve property
            logger.warning(f"Property '{prop_name}' not found.")
            break
        text = text.replace(match.group(0), prop_value)
    return text

# Function to parse pom.xml and extract dependencies and properties
def parse_pom(pom_path, properties):
    logger.debug(f"Parsing POM: {pom_path}")
    try:
        tree = ET.parse(pom_path)
        root = tree.getroot()
        ns = {'m': 'http://maven.apache.org/POM/4.0.0'}

        # Update properties with those defined in this POM
        properties_element = root.find('m:properties', ns)
        if properties_element is not None:
            for prop in properties_element:
                prop_name = prop.tag.replace('{http://maven.apache.org/POM/4.0.0}', '')
                prop_value = prop.text
                properties[prop_name] = resolve_properties(prop_value, properties)

        # Set default properties
        group_id_element = root.find('m:groupId', ns)
        if group_id_element is not None:
            properties['project.groupId'] = group_id_element.text
        else:
            # Try to get from parent
            parent = root.find('m:parent', ns)
            if parent is not None:
                parent_group_id = parent.find('m:groupId', ns).text
                properties['project.groupId'] = resolve_properties(parent_group_id, properties)

        version_element = root.find('m:version', ns)
        if version_element is not None:
            properties['project.version'] = version_element.text
        else:
            # Try to get from parent
            parent = root.find('m:parent', ns)
            if parent is not None:
                parent_version = parent.find('m:version', ns).text
                properties['project.version'] = resolve_properties(parent_version, properties)


        # Parse dependencies
        dependencies = []
        for dep in root.findall('.//m:dependencies/m:dependency', ns):
            group_id_element = dep.find('m:groupId', ns)
            artifact_id_element = dep.find('m:artifactId', ns)
            version_element = dep.find('m:version', ns)
            scope_element = dep.find('m:scope', ns)
            optional_element = dep.find('m:optional', ns)

            # Ensure elements are not None
            if group_id_element is None or artifact_id_element is None:
                logger.warning("Dependency missing groupId or artifactId. Skipping.")
                continue

            group_id = resolve_properties(group_id_element.text, properties)
            artifact_id = resolve_properties(artifact_id_element.text, properties)

            if version_element is not None and version_element.text is not None:
                version = resolve_properties(version_element.text, properties)
            else:
                # Try to get version from dependency management
                version = get_version_from_dependency_management(root, group_id, artifact_id, properties, ns)
                if version is None:
                    # Attempt to get the latest version from Maven Central
                    version = get_latest_version_from_maven_central(group_id, artifact_id)
                    if version is None:
                        logger.warning(f"No version specified for dependency {group_id}:{artifact_id} and failed to resolve from Maven Central. Skipping.")
                        continue
                    else:
                        logger.info(f"Resolved latest version for {group_id}:{artifact_id} as {version}")

            # Process scope and optional as before
            scope = scope_element.text if scope_element is not None else 'compile'
            if scope in ['test', 'provided']:
                continue  # Skip test and provided scopes

            if optional_element is not None and optional_element.text == 'true':
                continue  # Skip optional dependencies

            dependencies.append((group_id, artifact_id, version))

        # Handle modules
        modules = []
        # for module in root.findall('.//m:module', ns):
        #     if module.text:
        #         module_name = module.text.strip()
        #         modules.append(module_name)
        #         logger.info(f"Found module: {module_name}")

        # # Parse dependencies in dependencyManagement
        # dependency_management = root.find('m:dependencyManagement', ns)
        # if dependency_management is not None:
        #     managed_dependencies = dependency_management.findall('./m:dependencies/m:dependency', ns)
        #     for dep in managed_dependencies:
        #         group_id_elem = dep.find('m:groupId', ns)
        #         artifact_id_elem = dep.find('m:artifactId', ns)
        #         version_elem = dep.find('m:version', ns)

        #         if group_id_elem is not None and artifact_id_elem is not None and version_elem is not None:
        #             group_id = resolve_properties(group_id_elem.text, properties)
        #             artifact_id = resolve_properties(artifact_id_elem.text, properties)
        #             version = resolve_properties(version_elem.text, properties)
        #             # Store managed version
        #             properties[f'{group_id}:{artifact_id}:version'] = version
        #             logger.debug(f"Managed dependency: {group_id}:{artifact_id}:{version}")

        return dependencies, modules
    except ET.ParseError as e:
        logger.error(f"Failed to parse {pom_path}: {e}")
        return []

# Function to get version from dependencyManagement
def get_version_from_dependency_management(root, group_id, artifact_id, properties, ns):
    dependency_management = root.find('m:dependencyManagement', ns)
    if dependency_management is not None:
        dependencies = dependency_management.findall('.//m:dependency', ns)
        for dep in dependencies:
            dm_group_id = dep.find('m:groupId', ns)
            dm_artifact_id = dep.find('m:artifactId', ns)
            dm_version = dep.find('m:version', ns)
            if dm_group_id is not None and dm_artifact_id is not None and dm_version is not None:
                dm_group_id_text = resolve_properties(dm_group_id.text, properties)
                dm_artifact_id_text = resolve_properties(dm_artifact_id.text, properties)
                if dm_group_id_text == group_id and dm_artifact_id_text == artifact_id:
                    return resolve_properties(dm_version.text, properties)
    return None

def get_latest_version_from_maven_central(group_id, artifact_id):
    import requests

    # Construct the search query
    query = f'g:"{group_id}" AND a:"{artifact_id}"'
    params = {
        'q': query,
        'rows': 1,
        'wt': 'json',
        'core': 'gav'
    }
    search_url = 'https://search.maven.org/solrsearch/select'

    try:
        response = requests.get(search_url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        docs = data.get('response', {}).get('docs', [])
        if docs:
            latest_version = docs[0].get('v')
            return latest_version
        else:
            logger.warning(f"No versions found for {group_id}:{artifact_id} on Maven Central.")
            return None
    except requests.RequestException as e:
        logger.error(f"Failed to query Maven Central for {group_id}:{artifact_id}: {e}")
        return None


# Recursive function to download artifact and its dependencies

def download_artifact(group_id, artifact_id, version, dependencies_dir=DEPENDENCIES_DIR, processed=set()):
    key = (group_id, artifact_id)
    if key in processed:
        return
    processed.add(key)

    # Download the JAR
    jar_url = construct_maven_url(group_id, artifact_id, version, "jar")
    jar_dest = dependencies_dir / f"{artifact_id}-{version}.jar"
    logger.debug(f'Try download {jar_url} to {jar_dest}')
    if not download_file(jar_url, jar_dest):
        logger.warning(f"Failed to download JAR for {group_id}:{artifact_id}:{version}")        
        return

    # Download the POM
    pom_url = construct_maven_url(group_id, artifact_id, version, "pom")
    pom_dest = dependencies_dir / f"{artifact_id}-{version}.pom"
    if not download_file(pom_url, pom_dest):
        logger.warning(f"Failed to download POM for {group_id}:{artifact_id}:{version}")
        return

    # Parse the POM to find dependencies
    properties = {}  # Initialize properties for this POM
    dependencies, modules = parse_pom(pom_dest, properties)

    logger.debug(f"Processing modules for {modules}")
    # Recursively download dependencies
    for dep_group_id, dep_artifact_id, dep_version in dependencies:
        download_artifact(dep_group_id, dep_artifact_id, dep_version, dependencies_dir, processed)

    # Process modules
    
    for module_artifact_id in modules:
        # Assume groupId and version are same as parent
        module_group_id = properties.get('project.groupId')
        module_version = properties.get('project.version')
        if not module_group_id or not module_version:
            logger.warning(f"Cannot resolve groupId or version for module {module_artifact_id}. Skipping.")
            continue
        download_artifact(module_group_id, module_artifact_id, module_version)


def download_maria4j_jars(pom_file=Path(mariadb4y_root,'MariaDB4j','pom.xml'), dependencies_dir=DEPENDENCIES_DIR):
    properties = {} 
    if pom_file is not None and pom_file.exists():    
        logger.info(f'load dependency configurations from {pom_file}')    
        initial_dependencies=parse_pom(pom_file, properties)
    else:
        # List of initial dependencies to download
        initial_dependencies = [
            ("ch.vorburger.mariaDB4j", "mariaDB4j", "3.1.0")
        ]
    # Start downloading
    processed=set()
    for group_id, artifact_id, version in initial_dependencies:
        logger.info(f'Try download: {group_id}, {artifact_id}, {version}')
        download_artifact(group_id, artifact_id, version, dependencies_dir=dependencies_dir, processed=processed)

    logger.info("All dependencies downloaded.")
    return 'All dependencies downloaded.'
