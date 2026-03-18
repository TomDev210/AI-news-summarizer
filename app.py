from flask import Flask, request, render_template, flash, redirect, url_for
import nltk
from textblob import TextBlob
from newspaper import Article
from urllib.parse import urlparse
import validators
import requests
from googletrans import Translator
from nltk.tokenize import sent_tokenize
import os

nltk.download('punkt')

app = Flask(__name__)
app.secret_key = 'your_secret_key'

def get_website_name(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    if domain.startswith("www."):
        domain = domain[4:]
    return domain

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form['url']
        selected_lang = request.form['language']
        summary_type = request.form.get('summary_type', 'basic')

        if not validators.url(url):
            flash('Please enter a valid URL.')
            return redirect(url_for('index'))

        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.RequestException:
            flash('Failed to download the content of the URL.')
            return redirect(url_for('index'))

        article = Article(url)
        article.download()
        article.parse()

        article_text = article.text

        translator = Translator()
        try:
            article_text_en = translator.translate(article_text, src='auto', dest='en').text
        except Exception:
            flash('Translation failed. Please try again later.')
            return redirect(url_for('index'))

        # Sentence count based on summary type
        sentence_limit = 3 if summary_type == 'basic' else 7
        sentences = sent_tokenize(article_text_en)
        summary_en = ' '.join(sentences[:sentence_limit])

        # Translate summary to selected language
        if selected_lang != 'en':
            try:
                summary = translator.translate(summary_en, src='en', dest=selected_lang).text
            except Exception:
                flash('Summary translation failed. Showing English summary.')
                summary = summary_en
        else:
            summary = summary_en

        article.nlp()
        title = article.title
        authors = ', '.join(article.authors) or get_website_name(url)
        publish_date = article.publish_date.strftime('%B %d, %Y') if article.publish_date else "N/A"
        top_image = article.top_image

        analysis = TextBlob(article_text_en)
        polarity = analysis.sentiment.polarity
        sentiment = 'Positive 😊' if polarity > 0.1 else 'Negative 😟' if polarity < -0.1 else 'Neutral 😐'

        return render_template('index.html',
                               title=title,
                               authors=authors,
                               publish_date=publish_date,
                               summary=summary,
                               top_image=top_image,
                               sentiment=sentiment,
                               language=selected_lang)

    return render_template('index.html')

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
