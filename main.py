import io
import sys
import os
import uuid
from django.conf import settings
from django.core.management import execute_from_command_line
from django.http import JsonResponse, FileResponse
from django.shortcuts import render
from django.urls import path
from django.views.decorators.csrf import csrf_exempt
from gtts import gTTS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Forces all file generation to land inside the specific /audios subdirectory
AUDIO_DIR = os.path.join(BASE_DIR, "audios")

if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR)

SUPPORTED_LANGUAGES = {
    "en": "English",
    "fr": "French",
    "es": "Spanish",
    "de": "German",
    "ha": "Hausa",
}

# 1. RUNTIME CONFIGURATION INITIALIZATION
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY="standalone-tts-secret-auth-stringkey",
        ROOT_URLCONF=__name__,  
        BASE_DIR=BASE_DIR,
        TEMPLATES=[
            {
                "BACKEND": "django.template.backends.django.DjangoTemplates",
                "DIRS": [BASE_DIR],  
                "APP_DIRS": False,
            }
        ],
        MIDDLEWARE=[
            'django.middleware.common.CommonMiddleware',
        ]
    )

# 2. CORE BACKEND SYSTEM ENDPOINTS
@csrf_exempt
def convert_speech(request):
    audios = None
    error = None

    if request.method == "POST":
        user_text = request.POST.get("usertext", "").strip()
        language_choice = request.POST.get("language-selector")

        if not user_text:
            error = "Please enter some text."
        elif len(user_text.split()) > 200:
            error = "Text exceeds the maximum limit of 200 words."
        elif language_choice not in SUPPORTED_LANGUAGES:
            error = "Please select a valid language."
        else:
            filename = f"voice_{uuid.uuid4().hex}.mp3"
            # Target path updated to save files cleanly inside the audios subdirectory
            file_path = os.path.join(AUDIO_DIR, filename)
            try:
                to_speech = gTTS(text=user_text, lang=language_choice, slow=False)
                to_speech.save(file_path)
                audios = filename
            except Exception:
                error = "Something went wrong generating the audio. Try again."

    return render(request, "index.html", {
        "audios": audios, 
        "error": error, 
        "languages": SUPPORTED_LANGUAGES
    })

def play_audio(request, audios):
    safe_filename = os.path.basename(audios)
    # File streaming resolved from inside the audios subdirectory
    file_path = os.path.join(AUDIO_DIR, safe_filename)
    
    if os.path.exists(file_path):
        return FileResponse(open(file_path, "rb"), content_type="audio/mpeg")
    
    return JsonResponse({"error": "File not found"}, status=404)

# 3. INTERNAL ROUTER MAPPINGS
urlpatterns = [
    path("", convert_speech, name="convert_speech"),
    path("play/<str:audios>/", play_audio, name="play_audio"),
]

# 4. ENVIRONMENT RUNNER CONSOLE
if __name__ == "__main__":
    if len(sys.argv) == 1:
        sys.argv.extend(["runserver", "127.0.0.1:8000"]) 
    execute_from_command_line(sys.argv)
