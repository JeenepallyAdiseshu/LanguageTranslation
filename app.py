from flask import Flask, render_template, request
from langdetect import detect
from deep_translator import GoogleTranslator
from textblob import TextBlob

app = Flask(__name__)

languages = GoogleTranslator().get_supported_languages(as_dict=True)

@app.route("/", methods=["GET", "POST"])
def index():
    detected_lang = ""
    translated_text = ""
    text = ""
    target_lang = "english"
    word_count = 0
    char_count = 0
    sentiment = ""
    polarity = 0

    if request.method == "POST":
        text = request.form["text"]
        target_lang = request.form["target_lang"]

        # Language Detection
        detected_lang = detect(text)

        # Translation
        translated_text = GoogleTranslator(
            source='auto',
            target=target_lang
        ).translate(text)

        # Text Analytics
        word_count = len(text.split())
        char_count = len(text)

        blob = TextBlob(text)
        polarity = blob.sentiment.polarity

        if polarity > 0:
            sentiment = "Positive 😊"
        elif polarity < 0:
            sentiment = "Negative 😔"
        else:
            sentiment = "Neutral 😐"

    return render_template(
        "index.html",
        text=text,
        detected_lang=detected_lang,
        translated_text=translated_text,
        languages=languages,
        word_count=word_count,
        char_count=char_count,
        sentiment=sentiment,
        polarity=polarity
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

