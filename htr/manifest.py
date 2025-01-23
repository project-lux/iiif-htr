import json
import requests

def download_manifest(manifest_url):
    manifest = requests.get(manifest_url).json()
    return manifest

def load_manifest(input_manifest_path):
    """
    Load a IIIF manifest from a local file.

    This function takes a manifest ID and loads the corresponding IIIF manifest JSON file
    from the local filesystem. The manifest should be stored in the input/manifests directory.

    Args:
        input_id (str): ID or path of the manifest to load. If a full path is provided,
                       only the final segment after the last '/' will be used.

    Returns:
        dict: The parsed IIIF manifest as a Python dictionary

    Example:
        manifest = load_manifest("10015825")
        # Loads manifest from input/manifests/10015825
    """
    with open(input_manifest_path) as f:
        manifest = json.load(f)
    return manifest

def load_image(manifest, max_height=1000, max_width=1000):
    """
    Extract image URLs and metadata from a IIIF manifest.

    This function parses a IIIF manifest to extract image information from each canvas.
    For large images (>2500px in either dimension), it uses the IIIF image service
    to get a scaled version. For smaller images, it uses the direct image URL.

    Args:
        manifest (dict): A IIIF manifest dictionary containing image information

    Returns:
        list[tuple]: A list of tuples, where each tuple contains:
            - image_url (str): URL to access the image
            - height (int): Height of the image in pixels
            - width (int): Width of the image in pixels  
            - label (str): Label or title associated with the image, if available
    """
    images = []
    
    for canvas in manifest.get('items', []):
        # Get the first annotation which contains the image info
        try:
            annotation = canvas['items'][0]['items'][0]
            image_info = annotation['body']
            
            # Get image dimensions
            height = image_info.get('height', 0)
            width = image_info.get('width', 0)
            
            # Get the image URL
            if 'service' in image_info and (height > max_height or width > max_width):
                # For large images, use the IIIF service to get a scaled version
                service_url = image_info['service'][0]['@id']
                image_url = f"{service_url}/full/!{max_width},{max_height}/0/default.jpg"
            else:
                # Otherwise use the direct image URL
                image_url = image_info['id']
                
            # Get the label if available
            label = canvas.get('label', {}).get('none', [''])[0]
            
            images.append((image_url, height, width, label))
            
        except (KeyError, IndexError):
            continue
            
    return images

def save_image(image_url, image_path):
    """
    Save an image from a URL to a local file.

    This function downloads an image from a given URL and saves it to the specified local path.
    It uses the requests library to fetch the image data and writes the binary content to a file.

    Args:
        image_url (str): The URL of the image to download
        image_path (str): The local file path where the image should be saved

    Returns:
        None
    """
    response = requests.get(image_url)
    with open(image_path, 'wb') as f:
        f.write(response.content)
