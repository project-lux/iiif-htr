import vertexai
import openai
from google.auth import default, transport

# For docs on using OpenAI with Google:
# https://cloud.google.com/vertex-ai/generative-ai/docs/multimodal/call-vertex-using-openai-library#generativeaionvertexai_gemini_chat_completions_non_streaming-python_vertex_ai_sdk

def connect_to_client(location, project_id):
    """
    Connects to Google Cloud Platform and initializes Vertex AI and OpenAI clients.
    
    Returns:
        OpenAI client: Configured OpenAI client for making API calls to Vertex AI endpoints
    """

    vertexai.init(project=project_id, location=location)

    # Programmatically get an access token
    credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    auth_request = transport.requests.Request()
    credentials.refresh(auth_request)

    # # OpenAI Client
    client = openai.OpenAI(
        base_url=f"https://{location}-aiplatform.googleapis.com/v1beta1/projects/{project_id}/locations/{location}/endpoints/openapi",
        api_key=credentials.token,
    )
    return client