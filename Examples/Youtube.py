import os
from pytubefix import YouTube

# Get the path of the current directory
current_directory = os.path.dirname(os.path.realpath(__file__))
YouTube_path = os.path.join(current_directory, 'YouTube')

# Function to track download progress and display formatted size
def format_size(size):
    suffixes = ['B', 'KB', 'MB', 'GB', 'TB']  # List of suffixes for each size
    suffix_index = 0
    while size >= 1024 and suffix_index < len(suffixes) - 1:
        size /= 1024  # Divide the size by 1024 to convert to the next suffix
        suffix_index += 1
    return f"{size:.2f} {suffixes[suffix_index]}"

# Function to track download progress and display size in bytes, kilobytes, megabytes, or gigabytes
def on_progress(stream, chunk, remaining_bytes):
    total_size = stream.filesize
    downloaded_bytes = total_size - remaining_bytes
    percentage = downloaded_bytes / total_size * 100
    chunk_size_mb = len(chunk) / (1024 * 1024)  # Converting chunk size from bytes to megabytes
    total_size_formatted = format_size(total_size)
    downloaded_bytes_formatted = format_size(downloaded_bytes)
    
    # Check if the stream has the 'fps' property
    if hasattr(stream, 'fps'):
        fps = stream.fps
        print(f"Downloading... {percentage:.2f}% complete. Downloaded: {downloaded_bytes_formatted} / {total_size_formatted}. Chunk size: {chunk_size_mb:.2f} MB, FPS: {fps}")
    else:
        print(f"Downloading... {percentage:.2f}% complete. Downloaded: {downloaded_bytes_formatted} / {total_size_formatted}. Chunk size: {chunk_size_mb:.2f} MB")

def format_views(views):
    if views < 1000:
        # Less than 1,000
        return str(views)
    elif views < 1000000:
        # From 1,000 to 999,999
        return f"{views / 1000:.1f}K"
    elif views <= 1099000:
        # From 1,000,000 to 1,099,000
        return "1M"
    elif views < 1000000000:
        # From 1,100,000 to 999,999,999
        return f"{views / 1000000:.1f}M"
    elif views < 1000000000000:
        # From 1B to 1T
        return f"{views / 1000000000:.1f}B" if views == 1000000000 else f"{views / 1000000000:.1f}B"
    elif views < 1000000000000000:
        # From 1T to 999,999,999,999,999
        return f"{views / 1000000000000:.1f}T" if views == 1000000000000 else f"{views / 1000000000000:.1f}T"
    else:
        # More than 1Q
        return f"{views / 1000000000000000:.1f}Q"
    
def format_duration(seconds):
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    return "{:02}:{:02}:{:02}".format(int(hours), int(minutes), int(seconds))

def get_video_duration(youtube_url):
    yt = YouTube(youtube_url)
    duration_seconds = yt.length
    return duration_seconds

# Download the video with the highest resolution
def download_video(url):
    yt = YouTube(url, on_progress_callback=on_progress)
    title = yt.title
    views = format_views(yt.views)
    author = yt.author
    date = yt.publish_date
    duration_seconds = get_video_duration(yt.watch_url)
    formatted_duration = format_duration(duration_seconds)
    channel_link = yt.channel_url
    video_link = yt.watch_url
    print("\nChannel:", author)
    print("Video Title:", title)
    print("Duration:", formatted_duration)
    print("Views:", views)
    print("Published:", date)
    print(f"\nChannel Link: {channel_link} \n")
    print(f"Video Link: {video_link} \n")

    # Get all available streams
    streams = yt.streams

    # Remove 'none' streams and filter unique streams
    unique_streams = {}
    for stream in streams:
        if stream.resolution is not None:
            if stream.resolution not in unique_streams:
                unique_streams[stream.resolution] = stream
            elif stream.fps > unique_streams[stream.resolution].fps:
                unique_streams[stream.resolution] = stream

    # Sort resolution options
    streams = list(unique_streams.values())

    # Remove 'none' streams
    streams = [stream for stream in streams if stream.resolution is not None]

    # Sort resolution options by video size, from largest to smallest
    streams.sort(key=lambda x: x.filesize, reverse=True)

    # Show available quality options and their sizes
    print("Available Resolutions:")
    for i, stream in enumerate(streams):
        total_size_formatted = format_size(stream.filesize)
        fps = stream.fps
        if fps:
            print(f"{i+1}. Resolution: {stream.resolution}, FPS: {fps}, Format: {stream.mime_type}, Size: {total_size_formatted}")
        else:
            print(f"{i+1}. Resolution: {stream.resolution}, Format: {stream.mime_type}, Size: {total_size_formatted}")
    
    # Add option to download audio only
    print(f"{len(streams) + 1}. Download audio only")

    # Prompt the user to choose resolution or audio only
    while True:
        try:
            choice = int(input("Enter the number corresponding to the desired resolution or '0' to download audio only: "))
            if choice == len(streams) + 1:
                download_audio_only(url)
                return
            selected_stream = streams[choice - 1]
            break
        except (ValueError, IndexError):
            print("Invalid choice. Please enter a valid number.")

    # Download the video in the chosen resolution
    os.makedirs(YouTube_path, exist_ok=True)
    video_path = selected_stream.download(output_path=YouTube_path, filename=f"{yt.title}.webm")

    # Filter audio streams to remove those without sound
    audio_streams = [stream for stream in yt.streams.filter(only_audio=True) if stream.audio_codec is not None]
    if audio_streams:
        audio_stream = audio_streams[0]  # Select the first audio option (highest quality)
        audio_path = os.path.join(YouTube_path, f"{yt.title}.mp3")
        audio_stream.download(output_path=YouTube_path, filename=f"{yt.title}.mp3")
        print(f"Audio downloaded at: {audio_path}")
    else:
        print("Could not find an available audio option.")

    # Combine video and audio
    os.system(f"ffmpeg -i \"{video_path}\" -i \"{audio_path}\" -c:v copy -c:a aac -strict experimental \"{video_path[:-4]}.mp4\"")

    print(f"Video with audio downloaded at: {video_path[:-4]}.mp4")

def download_audio_only(url):
    yt = YouTube(url)
    print("Downloading only the audio of the video:", yt.title)
    # Filter audio streams to remove those without sound
    audio_streams = [stream for stream in yt.streams.filter(only_audio=True) if stream.audio_codec is not None]
    if audio_streams:
        audio_stream = audio_streams[0]  # Select the first audio option (highest quality)
        audio_path = os.path.join(YouTube_path, f"{yt.title}.mp3")
        audio_stream.download(output_path=YouTube_path, filename=f"{yt.title}.mp3")
        print(f"Audio downloaded at: {audio_path}")
    else:
        print("Could not find an available audio option.")

# Example usage
if __name__ == "__main__":
    url = input("Enter the YouTube URL: ")
    download_video(url)
