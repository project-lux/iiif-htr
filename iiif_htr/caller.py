import requests
from PIL import Image
from io import BytesIO
import base64
from datetime import datetime
from pydantic import BaseModel
import json
from typing import Optional, Literal

def get_image(image_url):
    """
    Download and process an image from a URL.

    This function downloads an image from a URL, resizes it if needed while maintaining
    aspect ratio, and converts it to bytes for model processing.

    Args:
        image_url (str or tuple): URL of the image to download. If tuple, first element is used as URL.

    Returns:
        bytes: Processed image as JPEG bytes, resized if original dimensions exceeded 1000px.
    """
    # Download and resize image
    if isinstance(image_url, tuple):
        image_url = image_url[0]  # Extract the URL from the tuple
    response = requests.get(image_url)
    img = Image.open(BytesIO(response.content))
    
    # Maintain aspect ratio while ensuring neither dimension exceeds 1000px
    max_size = 1000
    ratio = min(max_size/img.width, max_size/img.height)
    if ratio < 1:
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    
    # Save to bytes for sending to models
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()

    return img_byte_arr

def get_image_from_dir(image_path):
    """
    Get an image from a directory.
    """
    img = Image.open(image_path)
    # Maintain aspect ratio while ensuring neither dimension exceeds 1000px
    max_size = 1000
    ratio = min(max_size/img.width, max_size/img.height)
    if ratio < 1:
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    
    # Save to bytes for sending to models
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr = img_byte_arr.getvalue()
    return img_byte_arr

def model_call(
                     structured_prompt,
                     client,
                     data_model,
                     max_tokens=4000,
                     model="google/gemini-1.0-pro-vision",
                     method: Literal["transcription", "entities"] = "transcription",
                     temperature=0.5,
                     image_url=None,
                     image_path=None
                     ):
    """
    Make an API call to an AI model with a structured prompt.

    This function sends a structured prompt to an AI model and returns the parsed response.
    For transcription tasks, it processes an image first. For entity extraction tasks,
    it processes text directly.

    Args:
        structured_prompt (str): The formatted prompt to send to the model
        client: The configured AI client to use
        data_model: Pydantic model class to validate and parse the response
        max_tokens (int, optional): Maximum tokens in response. Defaults to 4000
        model (str, optional): Name of AI model to use. Defaults to "google/gemini-1.0-pro-vision"
        method (Literal["transcription", "entities"]): Type of task. Defaults to "transcription"
        temperature (float, optional): Sampling temperature. Defaults to 0.5
        image_url (str or tuple, optional): URL of image for transcription tasks.
            If tuple, first element is used as URL. Required for transcription method.

    Returns:
        dict: Validated response matching data_model schema. For failed parsing:
            - transcription (str): Raw model response
            - human_remains (None): Placeholder null value
    
    Raises:
        ValueError: If image_url is missing for transcription method or if response parsing fails
    """
    messages = [{
            "role": "user",
            "max_tokens": max_tokens,
            "response_format": {
                "type": "json_object"
            },
            "content": [
                {
                    "type": "text", 
                    "text": structured_prompt
                }
            ]
        }]
    
    if method=="transcription":
        if image_url:
            img_byte_arr = get_image(image_url)
        elif image_path:
            img_byte_arr = get_image_from_dir(image_path)
        else:
            raise ValueError("Image URL is required for transcription")
        messages[0]["content"].append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64.b64encode(img_byte_arr).decode('utf-8')}"
            }
        })
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    
    # Parse the JSON response into the Pydantic model
    try:
        response_text = response.choices[0].message.content
        # Clean the response in case the model includes markdown code blocks
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        return data_model.model_validate_json(response_text).model_dump()
    except Exception as e:
        return {
            "transcription": response.choices[0].message.content,
            "human_remains": None
        }

def build_description(data_model):
    """Build a formatted description string from a Pydantic model's fields.

    Args:
        data_model (BaseModel): A Pydantic model class to extract field descriptions from

    Returns:
        str: A formatted string containing field names, types and descriptions,
             with each field on a new line and properly indented
    """
    schema_description = "\n".join(
        f"        {field_name}: {field.annotation} - {field.description}"
        for field_name, field in data_model.model_fields.items()
    )
    return schema_description


def model_call_synthetic(client, model, data_model, schema_description, structured_prompt, max_tokens=4000, temperature=0.5):
    """
    Make an API call to an AI model with a structured prompt.
    """
    messages = [{
            "role": "user",
            "max_tokens": max_tokens,
            "response_format": {
                "type": "json_object"
            },
            "content": [
                {
                    "type": "text", 
                    "text": structured_prompt
                }
            ]
        }]
    response = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    try:
        response_text = response.choices[0].message.content
        # Clean the response in case the model includes markdown code blocks
        response_text = response_text.replace("```json", "").replace("```", "").strip()
        return data_model.model_validate_json(response_text).model_dump()
    except Exception as e:
        print("Failed to Match Schema")
        return None