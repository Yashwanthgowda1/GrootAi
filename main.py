
import os
from os import PathLike
from time import time
import asyncio
from typing import Union
from dotenv import load_dotenv
from openai import AzureOpenAI
from deepgram import Deepgram
import pygame
from pygame import mixer
import elevenlabs

from record import speech_to_text


# Load API keys
load_dotenv()
os.environ["OPEN_API_TYPE"]="azure"
os.environ["OPENAI_API_VERSION"]="2024-05-31"
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
elevenlabs.set_api_key(os.getenv("ELEVENLABS_API_KEY"))

# Initialize APIs
deepgram = Deepgram(DEEPGRAM_API_KEY)
client = AzureOpenAI(
    api_key="c9be1d23e6ae4a9db0b866531f5ef228",
    api_version="2023-12-01-preview",
    azure_endpoint="https://apx-hack24-avishkar.openai.azure.com/"
    )

# mixer is a pygame module for playing audio
mixer.init()

# Change the context if you want to change Groot's personality
context = "You are Groot, Akshay's human assistant. You are witty and full of personality and friendly nature. Your answers should be simple,also ask if you want some more information, and if asked you to explain anything explain it in simple language as you are explaning it to 5yr old child with an examples,dont speak your name untill and unless you are asked for,dont use symboles, use human like conversation,give answers in one single line don't seperate line,"
conversation = {"Conversation": []}
RECORDING_PATH = "audio/recording.wav"

def request_gpt(prompt: str) -> str:

    out = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": f"{prompt}",
            }
        ]
    )
    return out.choices[0].message.content


async def transcribe(
    file_name: Union[Union[str, bytes, PathLike[str], PathLike[bytes]], int]
):

    with open(file_name, "rb") as audio:
        source = {"buffer": audio, "mimetype": "audio/wav"}
        response = await deepgram.transcription.prerecorded(source,timeout=300)
        return response["results"]["channels"][0]["alternatives"][0]["words"]


def log(log: str):
    """
    Print and write to status.txt
    """
    print(log)
    with open("status.txt", "w") as f:
        f.write(log)


if __name__ == "__main__":
    while True:
        # Record audio
        log("Listening...")
        speech_to_text()
        log("Done listening")

        # Transcribe audio
        current_time = time()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        words = loop.run_until_complete(transcribe(RECORDING_PATH))
        string_words = " ".join(
            word_dict.get("word") for word_dict in words if "word" in word_dict
        )
        with open("conv.txt", "a") as f:
            f.write(f"{string_words}\n")
        transcription_time = time() - current_time
        log(f"Finished transcribing in {transcription_time:.2f} seconds.")

        # Get response from GPT-3
        current_time = time()
        context += f"\nAkshay: {string_words}\nGroot: "
        response = request_gpt(context)
        context += response
        gpt_time = time() - current_time
        log(f"Finished generating response in {gpt_time:.2f} seconds.")

        # Convert response to audio
        current_time = time()
        audio = elevenlabs.generate(
            text=response, voice="Adam", model="eleven_monolingual_v1"
        )
        elevenlabs.save(audio, "audio/response.wav")
        audio_time = time() - current_time
        log(f"Finished generating audio in {audio_time:.2f} seconds.")

        # Play response
        log("Speaking...")
        sound = mixer.Sound("audio/response.wav")
        # Add response as a new line to conv.txt
        with open("conv.txt", "a",encoding="utf-8") as f:
            f.write(f"{response}\n")
        sound.play()
        pygame.time.wait(int(sound.get_length() * 1000))
        print(f"\n --- USER: {string_words}\n --- GROOT: {response}\n")