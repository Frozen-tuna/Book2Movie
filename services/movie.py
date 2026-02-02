import base64
import os
from moviepy import AudioFileClip, ImageClip, concatenate_videoclips
from audio import string_to_audio

def build_movie(tomes, images, book_name, start, stop):
    clips = []
    for index, tome in enumerate(tomes):
        image = base64.b64decode(images[index])
        audio_segment = string_to_audio(tome["audio"])

        audio_file = "temp/temp_audio"+str(index)+".mp3"
        audio_segment.export(audio_file, format="mp3")
        with open("temp/temp_image.png", 'wb') as f:
            f.write(image)


        audio_clip = AudioFileClip(audio_file)
        image_clip = ImageClip("temp/temp_image.png", duration=audio_segment.duration_seconds)
        video_clip = image_clip.with_audio(audio_clip)
        clips.append(video_clip)
        os.remove(audio_file)

    final_clip = concatenate_videoclips(clips)

    # Write the final video to a file
    final_clip.write_videofile(book_name + "_" + str(start) + "_" + str(stop) + ".mp4", codec="libx264", audio_codec="aac", fps=1)