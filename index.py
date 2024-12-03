import os
import threading
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import subprocess

# Settings
input_directory = "input"
output_directory = "output"
num_threads = 2

# Functions
def get_file_size_in_mb(file_path):
    """Calculate file size in MB."""
    return os.path.getsize(file_path) / (1024 * 1024)


def process_total_time(input_file):
    """Extract the total duration of the video in seconds using FFmpeg."""
    try:
        probe = subprocess.check_output(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", input_file],
            text=True
        )
        return float(probe.strip())
    except Exception as e:
        print(f"Error getting duration for {input_file}: {e}")
        return 1.0

def scan_files(directory, extension=".ts"):
    """Scan the directory for files with the given extension."""
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(extension)]


def convert_ts_to_mp4(input_file, output_file, global_bar, lock, position):
    """Convert TS to MP4 and update the progress bars dynamically."""
    file_size_mb = get_file_size_in_mb(input_file)
    total_duration = process_total_time(input_file)

    progress_bar = tqdm(
        total=file_size_mb,
        desc=f"Processing {os.path.basename(input_file)}",
        unit="MB",
        position=position,
        leave=False,
    )

    try:
        process = subprocess.Popen(
            [
                "ffmpeg",
                "-i", input_file,
                "-c", "copy",
                "-progress", "pipe:1",
                "-loglevel", "error",
                output_file,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        processed_mb = 0
        for line in process.stdout:
            if "out_time_ms" in line:
                processed_time_ms = int(line.split("=")[1].strip())
                progress_ratio = processed_time_ms / 1_000_000 / total_duration
                new_processed_mb = progress_ratio * file_size_mb

                progress_bar.update(new_processed_mb - processed_mb)

                with lock:
                    global_bar.update(new_processed_mb - processed_mb)
                
                processed_mb = new_processed_mb

        process.wait()
        if process.returncode != 0:
            raise subprocess.SubprocessError(f"Error processing {input_file}")

    except Exception as e:
        print(f"Error converting {input_file}: {e}")

    progress_bar.close()

    with lock:
        print(f"\033[{position + 1}A\033[K", end="")


def main():
    ts_files = scan_files(input_directory)
    if not ts_files:
        print("No .ts files found in the input directory!")
        return

    total_size_mb = sum(get_file_size_in_mb(f) for f in ts_files)

    global_bar = tqdm(
        total=total_size_mb, desc="Global Progress", unit="MB", position=0, leave=True
    )

    lock = threading.Lock()

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for idx, input_file in enumerate(ts_files):
            output_file = os.path.join(
                output_directory, os.path.splitext(os.path.basename(input_file))[0] + ".mp4"
            )
            executor.submit(
                convert_ts_to_mp4,
                input_file,
                output_file,
                global_bar,
                lock,
                position=idx + 1,
            )

    global_bar.close()
    print(f"Conversion completed for {len(ts_files)} files!")

if __name__ == "__main__":
    main()