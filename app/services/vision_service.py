import os
import json
import mimetypes
from google import genai
from google.genai import types
from app.schemas import ImageMetadata
from app.config import settings

client = genai.Client(api_key=settings.GEMINI_API_KEY)

ESTIMATED_IMAGE_COST_USD = 0.0001 

def analyze_image_file(file_path: str) -> dict:
    """Sends an image to Gemini 2.5 Flash and extracts validated structured output."""
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = "image/jpeg"

    with open(file_path, "rb") as img_file:
        image_bytes = img_file.read()

    prompt = (
        "Analyze this image carefully. Extract the primary subject, main high-level category, "
        "key visual attributes, a descriptive caption, and your overall classification confidence score."
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[
            types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
            prompt
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ImageMetadata,
        ),
    )

    parsed_json = json.loads(response.text)
    validated_metadata = ImageMetadata(**parsed_json)

    # Flag low confidence results (< 0.70)
    is_flagged = validated_metadata.confidence < 0.70

    prompt_tokens = response.usage_metadata.prompt_token_count if response.usage_metadata else 258
    completion_tokens = response.usage_metadata.candidates_token_count if response.usage_metadata else 50

    return {
        "metadata": validated_metadata,
        "flagged": is_flagged,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "cost_usd": ESTIMATED_IMAGE_COST_USD
    }