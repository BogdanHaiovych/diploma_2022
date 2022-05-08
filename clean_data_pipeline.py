# Preprocess texts

### Clean texts

import re

import demoji
import pandas as pd
import re
import string
import cld2
from numpy import isin
import nltk
nltk.download('stopwords')
from nltk.corpus import stopwords
from lemmatization import process, process_pipeline


# demoji.download_codes()

whitespace = re.compile("[\s\u0020\u00a0\u1680\u180e\u202f\u205f\u3000\u2000-\u200a]+", re.UNICODE)

def simple_tokenize(text, max_shrink=False):
    """
    Tokenizer for sentiment analysis of mentions (MOSTLY Facebook text)
    """
#     delete urls
    clean_text = re.sub(r'http\S+', ' ', text)
#     delete everything in brackets -- <>
    clean_text = re.sub(r"</?\w*>", " ", clean_text)
#     delete
    for c in ["(", ")", "!", "?", r"-", r"*", ".", ",", r'"']:
        clean_text = re.sub("[%s]+" % c, c, clean_text)

#     delete hashtags
    clean_text = re.sub(r"#\w*|№\w*", " ", clean_text)
    
#     delete complex model names
    clean_text = re.sub(r"\b\S+[0-9]+\S+\b", " ", clean_text)

    if clean_text == '':
        return "NULL"

    clean_text = clean_text.replace("\n", ' ')
    clean_text = clean_text.replace("\b", " ")
    clean_text = clean_text.replace("=", " ")
    clean_text = clean_text.replace("+", " ")

    # add spaces around punctuation
    chars = string.punctuation
    chars = chars.replace("`", "")
    chars = chars.replace("'", "")
    chars += "«»\"“”‘’.?!…,:;"

    for c in chars:
        clean_text = clean_text.replace(c, ' ')

#     delete emojis
    clean_text = demoji.replace(clean_text)
#     remove digits
    clean_text = ''.join(ch for ch in clean_text if ch not in string.digits)
#     set to lowercase
    clean_text = clean_text.lower()

    if clean_text.replace(' ', '') == '':
        return "NULL"

    only_letters = re.sub(f"[0-9]|[{chars}]|\s", "", clean_text)

    if only_letters == '' or len(only_letters) == 0:
        return "NULL"
    else:
        if max_shrink:
            return re.sub(f"[0-9]|[{chars}]", "", clean_text)
        else:
            return clean_text


def squeeze_whitespace(input_):
    return whitespace.sub(" ", input_).strip()


def tokenize(text, max_shrink=False):
    """
    Function refers to splitting up a larger body of text into words
    text: parameter takes sentence
    max_shrink: leaves only letters
    """
    try:
        assert isinstance(text, str)
    except AssertionError:
        return None
    else:
        return squeeze_whitespace(simple_tokenize(text, max_shrink))


def predict_languages_with_cld2(text):
    """
    # BROKEN LOGIC
    text: str
    """
    assert isinstance(text, str)

    try:
        output = cld2.detect(text)
    except ValueError:
        return "Unknown"

    pred_lang = output.details[0].language_name
    if pred_lang == "RUSSIAN":
        return "ru"
    elif pred_lang == "UKRAINIAN":
        return "uk"
    elif pred_lang == "ENGLISH":
        return "en"
    else:
        return "Unknown"


def main(df):
    df["clean_text"] = df.text.apply(lambda x: tokenize(x))

    df = df[df.clean_text != "NULL"]

    df.dropna(subset=["clean_text"], inplace=True)

    df.tail()

    ### Predict languages
    df['lang'] = df.clean_text.apply(lambda x: predict_languages_with_cld2(x))

    df.lang.value_counts()

    df[df.lang == "uk"].sample(10)[["text", "clean_text"]]


    df = df[isin(df.lang.tolist(), ["ru", "uk"])]
    ### Translate
    # translated texts
    df_rus = pd.read_excel(r"C:\Users\BHaiov01\Documents\Projects\Analysis\gorenje_2022\translations\november\gorenje_ready_for_translation.xlsx", 
                        index_col=0)
    print(f"Loaded {df_rus.shape[0]} translated rows")

    # print(df_rus.columns)

    df_rus = df_rus[isin(df_rus.index, df.index)]

    df_rus["clean_rus"] = df_rus.translated_text.apply(lambda x: tokenize(x))

    ### Remove stopwords

    with open("helpdata/stop_words_russian.txt", "r") as f:
        words = [w.replace("\n", "") for w in f.readlines()]
    #     print(words[:10])

    c = 0
    for w in stopwords.words("russian"):
        if w in words:
            c += 1
        else:
            words.append(w)
    #         print(w)
    print("Total number of stopwords is", len(words))

    df_rus.tail()

    df_rus["clean_rus_no_stopwords"] = df_rus.clean_rus.apply(lambda x: " ".join([w for w in x.split() if w not in words]))

    df_rus.head()

    df_rus["index"] = df_rus.index

    ### Lemmatization
    lemmatized = {}

    # {texd index : [list of lemmatized words], ...}
    for index, text in zip(df_rus.index, df_rus.clean_rus_no_stopwords.tolist()):
        lemmatized[index] = process(process_pipeline, text, keep_pos=False)
        lemmatized[index] = " ".join([w for w in lemmatized[index].split(" ") if w not in words])

    df_rus["lemmatized"] = None

    for index in df_rus.index:
        df_rus.loc[index, "lemmatized"] = " ".join(lemmatized[index])

    return df, df_rus