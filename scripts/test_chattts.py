"""Test ChatTTS loading and synthesis"""
import ChatTTS
import torch
import numpy as np
import sys

print("Creating Chat...")
sys.stdout.flush()
chat = ChatTTS.Chat()

print("Loading model (source='huggingface')...")
sys.stdout.flush()
try:
    ok = chat.load(compile=False, source="huggingface")
    print(f"Load result: {ok}")
    if chat.gpt:
        print("gpt: YES")
    else:
        print("gpt: NO")
    if chat.vocos:
        print("vocos: YES")
    else:
        print("vocos: NO")
    if chat.tokenizer:
        print("tokenizer: YES")
    else:
        print("tokenizer: NO")
except Exception as e:
    print(f"Load failed with huggingface: {type(e).__name__}: {e}")
    print("Trying with source='local'...")
    try:
        ok = chat.load(compile=False, source="local")
        print(f"Local load result: {ok}")
    except Exception as e2:
        print(f"Local load also failed: {type(e2).__name__}: {e2}")

if chat.gpt and chat.vocos and chat.tokenizer:
    print("\nModel loaded! Synthesizing...")
    sys.stdout.flush()
    wavs = chat.infer(["欢迎来到东方明珠广播电视塔，上海的地标性建筑。"], use_decoder=True)
    print(f"Generated audio shape: {wavs[0].shape}")
    print("SUCCESS!")
else:
    print("\nModel not fully loaded, cannot synthesize.")
