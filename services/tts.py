from gtts import gTTS


def text_to_speech(text, lang='es', slow=False):
    tts = gTTS(text=text, lang=lang, slow=slow)
    # tts.save("sound.mp3")
    return tts
