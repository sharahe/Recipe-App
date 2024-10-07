from app import app, client
from youtube_transcript_api import YouTubeTranscriptApi
from urllib.parse import urlparse
from urllib.parse import parse_qs
from flask import request


@app.route("/generate_tips", methods=["POST"])
def generate_tips():
    content = request.json
    print(content["url"])

    url = content["url"]
    parsed_url = urlparse(url)
    video_id = parse_qs(parsed_url.query)["v"][0]

    transcript_api = YouTubeTranscriptApi.get_transcript(video_id)
    transcript_str = ""
    for i in transcript_api:
        transcript_str += " " + i["text"]
    # print(transcript_str)

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": """Identify and Summarize the top 3 tips covered in this youtube recipe tutorial transcript about making New York Pizza. Only use the message provided below to summarize: {}""".format(
                    transcript_str,
                ),
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "video_tips",
                "schema": {
                    "type": "object",
                    "properties": {
                        "recipe_tips": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "tip_number": {"type": "number"},
                                    "tip_msg": {"type": "string"},
                                    "reasoning": {"type": "string"},
                                },
                                "required": ["tip_number", "tip_msg", "reasoning"],
                                "additionalProperties": False,
                            },
                        },
                    },
                    "required": ["recipe_tips"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        },
    )
    print(completion)
    return completion.choices[0].message.content
