import ffmpeg
import os
import threading
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import time

# Settings
input_directory = "input"
output_directory = "output"
num_threads = 2
last_used_threads = num_threads

def convert_ts_to_mp4(input_file, output_file):
    try:
        (
            ffmpeg
            .input(input_file)
            .output(output_file, codec='copy')
            .global_args('-loglevel', 'error')
            .run(overwrite_output=True)
        )
    except ffmpeg.Error as e:
        print(f"Error while converting {input_file}: {e}")

def process_file(input_file, output_dir, progress_bar):
    filename = os.path.basename(input_file)
    output_file = os.path.join(output_dir, os.path.splitext(filename)[0] + ".mp4")
    convert_ts_to_mp4(input_file, output_file)
    progress_bar.update(1)

def scan_files(directory, extension=".ts"):
    return [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(extension)]

def main():
    global num_threads
    ts_files = scan_files(input_directory)
    total_files = len(ts_files)

    if total_files == 0:
        print("No .ts files found in the input directory!")
        return

    progress_bar = tqdm(total=total_files, desc="Converting TS to MP4", unit="file")

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        for input_file in ts_files:
            executor.submit(process_file, input_file, output_directory, progress_bar)

    progress_bar.close()
    print("Conversion completed!")

def save_last_thread_settings():
    global last_used_threads
    last_used_threads = num_threads
    print(f"Saved the last used thread count: {last_used_threads}")

def adjust_thread_count(new_thread_count):
    global num_threads
    num_threads = new_thread_count
    save_last_thread_settings()

if __name__ == "__main__":
    start_time = time.time()
    
    main()
    
    end_time = time.time()
    print(f"Total time taken: {end_time - start_time:.2f} seconds")