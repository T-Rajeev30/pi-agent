import subprocess
import os

def convert_to_mp4(input_file):
    output = input_file.replace(".h264", ".mp4")

    print("Converting →", output)

    subprocess.run([
        "ffmpeg",
        "-y",
        "-fflags", "+genpts",
        "-r", "60",
        "-i", input_file,
        "-c:v", "copy",
        "-movflags", "+faststart",
        output
    ])

    os.remove(input_file)
    return output
