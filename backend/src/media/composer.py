from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path


class Composer:
    def __init__(self, object_store) -> None:
        self.object_store = object_store
        self.transition_duration = 0.4

    def compose_text(self, shot_files: list[dict]) -> str:
        content = ['DEMO FINAL VIDEO', '================']
        for item in shot_files:
            content.append(f"Shot {item['sequence']}: {item['path']}")
        return '\n'.join(content)

    def compose_video(self, shot_files: list[dict], options: dict | None = None) -> dict:
        options = options or {}
        playable = [item for item in shot_files if str(item.get('path', '')).lower().endswith('.mp4')]
        if not playable:
            raise ValueError('No playable rendered shots available')

        with tempfile.TemporaryDirectory() as tempdir:
            temp_root = Path(tempdir)
            processed_inputs: list[dict] = []

            for index, item in enumerate(playable, start=1):
                local_input = temp_root / f'shot-{index:03d}.mp4'
                local_input.write_bytes(self.object_store.read_bytes(item['path']))
                processed_output = temp_root / f'processed-{index:03d}.mp4'
                processed = self._prepare_shot(local_input, processed_output, item, temp_root, index, options)
                processed_inputs.append(processed)

            output = temp_root / 'final-video.mp4'
            bgm_path = self._resolve_background_music(
                temp_root,
                sum(item['duration'] for item in processed_inputs),
                options,
            )
            self._compose_timeline(processed_inputs, output, bgm_path, options)
            metadata = self._probe(output)
            return {
                'bytes': output.read_bytes(),
                'duration': int(round(float(metadata.get('duration') or 0))),
                'resolution': metadata.get('resolution') or 'unknown',
                'segments': len(processed_inputs),
                'features': self._features(options, bgm_path),
                'bgm_source': self._bgm_source(options, bgm_path),
            }

    def _prepare_shot(self, input_path: Path, output_path: Path, shot: dict, temp_root: Path, index: int, options: dict) -> dict:
        metadata = self._probe(input_path)
        subtitle_text = str(shot.get('subtitle_text') or '').strip() if options.get('enable_subtitles', True) else ''
        voice_text = self._voiceover_text(shot) if options.get('enable_voiceover', True) else ''
        voiceover_path = self._synthesize_voiceover(
            voice_text,
            str(shot.get('voiceover_tone') or ''),
            temp_root / f'voiceover-{index:03d}.aiff',
        ) if voice_text else None

        command = ['ffmpeg', '-y', '-loglevel', 'error', '-i', str(input_path)]
        input_count = 1
        has_audio = bool(metadata.get('has_audio'))
        silent_input_index = None
        voice_input_index = None

        if not has_audio:
            silent_input_index = input_count
            command.extend([
                '-f',
                'lavfi',
                '-t',
                f"{max(float(metadata.get('duration') or 0), 0.1):.3f}",
                '-i',
                'anullsrc=channel_layout=stereo:sample_rate=44100',
            ])
            input_count += 1

        if voiceover_path:
            voice_input_index = input_count
            command.extend(['-i', str(voiceover_path)])

        filter_parts = []
        video_label = '0:v'
        if subtitle_text:
            subtitle_file = temp_root / f'subtitle-{index:03d}.txt'
            subtitle_file.write_text(subtitle_text, encoding='utf-8')
            filter_parts.append(
                f"[0:v]drawtext={self._drawtext_args(subtitle_file)}[vout]"
            )
            video_label = 'vout'

        audio_label = None
        base_audio_label = '0:a' if has_audio else f'{silent_input_index}:a'
        if voice_input_index is not None:
            filter_parts.extend([
                f"[{base_audio_label}]volume=0.45[basea]",
                f"[{voice_input_index}:a]volume=1.3[voicea]",
                '[basea][voicea]amix=inputs=2:weights=0.7 1.0:duration=first:normalize=0[aout]',
            ])
            audio_label = 'aout'
        elif not has_audio:
            filter_parts.append(f'[{silent_input_index}:a]anull[aout]')
            audio_label = 'aout'

        if filter_parts:
            command.extend(['-filter_complex', ';'.join(filter_parts)])

        command.extend(['-map', f'[{video_label}]' if video_label != '0:v' else '0:v'])
        if audio_label:
            command.extend(['-map', f'[{audio_label}]'])
        else:
            command.extend(['-map', '0:a'])

        command.extend([
            '-c:v',
            'libx264',
            '-preset',
            'veryfast',
            '-pix_fmt',
            'yuv420p',
            '-c:a',
            'aac',
            '-shortest',
            str(output_path),
        ])
        self._run(command, 'ffmpeg failed to prepare shot video')
        prepared = self._probe(output_path)
        return {
            'path': output_path,
            'duration': float(prepared.get('duration') or metadata.get('duration') or 0),
        }

    def _compose_timeline(self, clips: list[dict], output: Path, bgm_path: Path | None, options: dict) -> None:
        command = ['ffmpeg', '-y', '-loglevel', 'error']
        for clip in clips:
            command.extend(['-i', str(clip['path'])])
        if bgm_path:
            command.extend(['-i', str(bgm_path)])

        transitions_enabled = bool(options.get('enable_transitions', True))

        if len(clips) == 1:
            filter_parts = ['[0:v]setpts=PTS-STARTPTS[vout]']
            main_audio_label = '0:a'
        elif not transitions_enabled:
            filter_parts = [
                ''.join(f'[{index}:v][{index}:a]' for index in range(len(clips))) + f'concat=n={len(clips)}:v=1:a=1[vout][maina]'
            ]
            main_audio_label = 'maina'
        else:
            filter_parts = []
            current_video = '0:v'
            current_audio = '0:a'
            elapsed = clips[0]['duration']
            for index in range(1, len(clips)):
                next_video = f'{index}:v'
                next_audio = f'{index}:a'
                video_out = f'vxf{index}'
                audio_out = f'axf{index}'
                offset = max(elapsed - self.transition_duration, 0)
                filter_parts.append(
                    f'[{current_video}][{next_video}]xfade=transition=fade:duration={self.transition_duration}:offset={offset:.3f}[{video_out}]'
                )
                filter_parts.append(
                    f'[{current_audio}][{next_audio}]acrossfade=d={self.transition_duration}:curve1=tri:curve2=tri[{audio_out}]'
                )
                current_video = video_out
                current_audio = audio_out
                elapsed = elapsed + clips[index]['duration'] - self.transition_duration
            filter_parts.append(f'[{current_video}]setpts=PTS-STARTPTS[vout]')
            main_audio_label = current_audio

        if bgm_path:
            bgm_index = len(clips)
            filter_parts.extend([
                f'[{main_audio_label}]volume=1.0[maina]',
                f'[{bgm_index}:a]volume=0.16[bgma]',
                '[maina][bgma]amix=inputs=2:weights=1.0 0.18:duration=first:normalize=0[aout]',
            ])
        else:
            filter_parts.append(f'[{main_audio_label}]anull[aout]')

        command.extend([
            '-filter_complex',
            ';'.join(filter_parts),
            '-map',
            '[vout]',
            '-map',
            '[aout]',
            '-c:v',
            'libx264',
            '-preset',
            'veryfast',
            '-pix_fmt',
            'yuv420p',
            '-c:a',
            'aac',
            '-movflags',
            '+faststart',
            str(output),
        ])
        self._run(command, 'ffmpeg failed to compose final video')

    def _resolve_background_music(self, temp_root: Path, duration: float, options: dict) -> Path | None:
        if not options.get('enable_bgm', True):
            return None
        custom_bgm_path = str(options.get('bgm_path') or '').strip()
        if custom_bgm_path:
            suffix = Path(custom_bgm_path).suffix or '.m4a'
            output = temp_root / f'custom-bgm{suffix}'
            try:
                output.write_bytes(self.object_store.read_bytes(custom_bgm_path))
                return output
            except Exception:
                pass
        return self._generate_background_music(temp_root / 'bgm.m4a', duration)

    def _generate_background_music(self, output: Path, duration: float) -> Path | None:
        duration = max(float(duration or 0), 0.1)
        fade_out_start = max(duration - 1.2, 0)
        command = [
            'ffmpeg',
            '-y',
            '-loglevel',
            'error',
            '-f',
            'lavfi',
            '-i',
            f'sine=frequency=261.63:duration={duration:.3f}:sample_rate=44100',
            '-f',
            'lavfi',
            '-i',
            f'sine=frequency=329.63:duration={duration:.3f}:sample_rate=44100',
            '-f',
            'lavfi',
            '-i',
            f'sine=frequency=392.00:duration={duration:.3f}:sample_rate=44100',
            '-filter_complex',
            (
                '[0:a]volume=0.020[a0];'
                '[1:a]volume=0.014[a1];'
                '[2:a]volume=0.010[a2];'
                '[a0][a1][a2]amix=inputs=3:normalize=0,'
                'afade=t=in:st=0:d=0.8,'
                f'afade=t=out:st={fade_out_start:.3f}:d=1.2[aout]'
            ),
            '-map',
            '[aout]',
            '-c:a',
            'aac',
            str(output),
        ]
        try:
            self._run(command, 'ffmpeg failed to generate background music')
        except RuntimeError:
            return None
        return output

    def _voiceover_text(self, shot: dict) -> str:
        parts = [str(shot.get('dubbing_text') or '').strip(), str(shot.get('voiceover_text') or '').strip()]
        return '。'.join(part for part in parts if part)

    def _features(self, options: dict, bgm_path: Path | None) -> list[str]:
        features = []
        if options.get('enable_subtitles', True):
            features.append('subtitles')
        if options.get('enable_voiceover', True):
            features.append('voiceover_mix')
        if bgm_path and options.get('enable_bgm', True):
            features.append('background_music')
        if options.get('enable_transitions', True):
            features.append('fade_transition')
        return features

    def _bgm_source(self, options: dict, bgm_path: Path | None) -> str:
        if not bgm_path or not options.get('enable_bgm', True):
            return 'disabled'
        if options.get('bgm_path'):
            return 'custom'
        return 'generated'

    def _synthesize_voiceover(self, text: str, tone: str, output: Path) -> Path | None:
        if not text.strip() or shutil.which('say') is None:
            return None
        commands = self._say_commands(text, tone, output)
        for command in commands:
            try:
                self._run(command, 'say failed to synthesize voiceover')
                if output.exists() and output.stat().st_size > 0:
                    return output
            except RuntimeError:
                continue
        return None

    def _say_commands(self, text: str, tone: str, output: Path) -> list[list[str]]:
        rate = '185'
        tone_text = tone.lower()
        if '沉稳' in tone or '低沉' in tone:
            rate = '160'
        elif '轻快' in tone or '明亮' in tone:
            rate = '205'

        preferred_voice = None
        if '男' in tone:
            preferred_voice = 'Tingting'
        elif '女' in tone:
            preferred_voice = 'Tingting'
        elif '中文' in tone or '国语' in tone or '普通话' in tone:
            preferred_voice = 'Tingting'
        elif 'english' in tone_text:
            preferred_voice = 'Samantha'

        commands = []
        if preferred_voice:
            commands.append(['say', '-v', preferred_voice, '-r', rate, '-o', str(output), text])
        commands.append(['say', '-r', rate, '-o', str(output), text])
        return commands

    def _drawtext_args(self, subtitle_file: Path) -> str:
        options = [
            f"textfile='{self._ffmpeg_escape_path(subtitle_file)}'",
            'reload=1',
            'fontcolor=white',
            'fontsize=24',
            'line_spacing=6',
            'x=(w-text_w)/2',
            'y=h-text_h-42',
            'borderw=2',
            'bordercolor=black',
            'box=1',
            'boxcolor=0x00000088',
            'boxborderw=14',
        ]
        font_file = self._font_file()
        if font_file:
            options.insert(0, f"fontfile='{self._ffmpeg_escape_path(font_file)}'")
        return ':'.join(options)

    def _font_file(self) -> Path | None:
        candidates = [
            Path('/System/Library/Fonts/PingFang.ttc'),
            Path('/System/Library/Fonts/Hiragino Sans GB.ttc'),
            Path('/Library/Fonts/Arial Unicode.ttf'),
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    def _ffmpeg_escape_path(self, path: Path) -> str:
        return path.as_posix().replace('\\', '\\\\').replace(':', '\\:').replace("'", "\\'")

    def _probe(self, path: Path) -> dict:
        command = [
            'ffprobe',
            '-v',
            'error',
            '-show_entries',
            'format=duration:stream=codec_type,width,height',
            '-of',
            'json',
            str(path),
        ]
        result = self._run(command, 'ffprobe failed to inspect final video')
        payload = json.loads(result.stdout or '{}')
        streams = payload.get('streams', [])
        video_stream = next((item for item in streams if item.get('codec_type') == 'video'), {})
        width = video_stream.get('width')
        height = video_stream.get('height')
        resolution = f'{width}x{height}' if width and height else ''
        return {
            'duration': payload.get('format', {}).get('duration'),
            'resolution': resolution,
            'has_audio': any(item.get('codec_type') == 'audio' for item in streams),
        }

    def _run(self, command: list[str], fallback_message: str) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(command, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as error:
            message = error.stderr.strip() or error.stdout.strip() or fallback_message
            raise RuntimeError(message) from error
