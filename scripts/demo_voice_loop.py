from rich.console import Console
from rich.panel import Panel

from shrike7.asr import SpeechDetector
from shrike7.asr.robust_asr import RobustASR
from shrike7.asr.whisper_onnx import VietnameseASR
from shrike7.core import EndpointConfig, SoundDevicePlayer, record_until_silence
from shrike7.core.pipeline import VoicePipeline
from shrike7.llm import VietnameseLLM
from shrike7.tts import VietnameseTTS

console = Console()

detector = SpeechDetector()
asr = RobustASR(asr=VietnameseASR(), vad=detector)
llm = VietnameseLLM(n_threads=8, n_gpu_layers=-1)
tts = VietnameseTTS(voice="NF")
player = SoundDevicePlayer()

pipeline = VoicePipeline(asr=asr, llm=llm, tts=tts)
config = EndpointConfig(endpoint_silence_ms=700, max_record_ms=10000)

while True:
    input("\nPress ENTER and speak. Ctrl+C to quit.")
    audio = record_until_silence(detector, config=config)

    for event in pipeline.turn_streaming(audio, audio_sink=player):
        if event.type == "asr":
            console.print(Panel(event.text or "<empty>", title="ASR"))
        elif event.type == "audio":
            console.print(f"[dim]Played chunk:[/dim] {event.text}")
        elif event.type == "tts":
            ttfa_ms = event.metadata.get("ttfa_ms") if event.metadata else None
            suffix = f" ({ttfa_ms:.0f} ms TTFA)" if ttfa_ms is not None else ""
            console.print(f"[green]Speaking chunk:[/green] {event.text}{suffix}")
        elif event.type == "error":
            console.print(f"[red]Streaming error:[/red] {event.text}")
        elif event.type == "done":
            console.print(f"\n[dim]Done in {event.latency_ms:.0f} ms[/dim]")
