from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import moviepy.editor as mp
import os
import tempfile

app = FastAPI()

# Define a folder where the videos will be saved
VIDEO_SAVE_FOLDER = 'videos'
os.makedirs(VIDEO_SAVE_FOLDER, exist_ok=True)

# Allowed image content types
ALLOWED_IMAGE_TYPES = {
    'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'
}

@app.post("/api/v1/audio-to-video/")
async def create_video(audio_file: UploadFile = File(...), image_file: UploadFile = File(...)):
    # Validate audio file type
    if not audio_file.content_type.startswith('audio/') or audio_file.content_type != 'audio/mpeg':
        raise HTTPException(status_code=400, detail="Invalid audio file format. Only MP3 is allowed.")

    # Validate image file type
    if image_file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(status_code=400, detail="Invalid image file format. Allowed formats: JPG, JPEG, PNG, GIF, WEBP.")

    # Read the audio file and image file from the request
    audio_data = await audio_file.read()
    image_data = await image_file.read()

    # Create temporary files for audio and image
    audio_temp_file_path = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name
    image_temp_file_path = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg").name

    with open(audio_temp_file_path, 'wb') as audio_temp_file:
        audio_temp_file.write(audio_data)

    with open(image_temp_file_path, 'wb') as image_temp_file:
        image_temp_file.write(image_data)

    try:
        # Create MoviePy clips
        audio_clip = mp.AudioFileClip(audio_temp_file_path)
        image_clip = mp.ImageClip(image_temp_file_path)
        
        # Set the duration of the image clip to match the duration of the audio clip
        image_clip = image_clip.set_duration(audio_clip.duration).set_fps(24)
        
        # Create the video with the image and the audio
        video_clip = image_clip.set_audio(audio_clip)

        # Define a path for the output video file
        output_video_path = os.path.join(VIDEO_SAVE_FOLDER, 'output_video.mp4')
        
        # Save the video to the defined path
        video_clip.write_videofile(output_video_path, codec='libx264', audio_codec='aac', fps=24)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating video: {str(e)}")

    finally:
        # Clean up temporary files
        os.remove(audio_temp_file_path)
        os.remove(image_temp_file_path)

    # Return the complete file path in a JSON response
    complete_path = os.path.abspath(output_video_path)
    return JSONResponse(status_code=201, content={"file_path": complete_path})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
