"""Build safe FFmpeg arguments for supported playback-speed presets."""


_SPEED_PRESETS = {
    "0.5": 2.0,
    "0.75": 1.35,
    "1.5": 0.68,
    "2.0": 0.5,
}


def build_ffmpeg_speed_args(input_path, output_path, speed, is_video):
    """Return argument-vector values; never construct a shell command."""
    speed = str(speed)
    if speed not in _SPEED_PRESETS:
        raise ValueError(f"Unsupported playback speed: {speed}")

    args = ["-y", "-i", str(input_path)]
    if is_video:
        args.extend(["-filter:v", f"setpts={_SPEED_PRESETS[speed]}*PTS"])
    args.extend(["-filter:a", f"atempo={speed}", str(output_path)])
    return args
