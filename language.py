import cld2
import enchant
import re
import os
from tools.dataprocessing import tokenize
from google.cloud import translate_v2 as translate
from pyaspeller import YandexSpeller


__all__ = ["correct_message", "predict_languages_with_cld2", "detect_language"]

en_dict = enchant.Dict("en_US")
ru_dict = enchant.Dict("ru_RU")
# uk_dict = enchant.Dict("uk_UA")


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


def is_russian(word):
    if bool(re.search(r'[а-яё]+', word)) and (ru_dict.check(word) or ru_dict.check(word[0].upper() + word[1:])):
        return True
    return False


def is_ukrainian(word):
    if bool(re.search(r'[а-яієїґ]+', word)) and (uk_dict.check(word) or uk_dict.check(word[0].upper() + word[1:])):
        return True
    return False


def use_google(key_path=r"C:\Users\b.haiovych\Documents\Projects\senti-amplifi\fluid-honor-308514-f136783c5202.json"):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path


def detect_language_with_google(text):
    """Detects the text's language."""
#     from google.cloud import translate_v2 as translate

    translate_client = translate.Client()

    # Text can also be a sequence of strings, in which case this method
    # will return a sequence of results for each text.
    result = translate_client.detect_language(text)

#     print("Text: {}".format(text))
#     print("Confidence: {}".format(result["confidence"]))
#     print("Language: {}".format(result["language"]))
    return result


def detect_language(text):
    """
    Function determines the language of the text

    text: str -- one sentence at a time
    """
    lang = predict_languages_with_cld2(text)

    if lang == "Unknown":
        shrinked = tokenize(text, True)
        # counters
        u = 0
        r = 0
        o = 0
        for word in shrinked.split():
            if bool(word.isalpha()):
                if is_ukrainian(word):
                    u += 1
                elif is_russian(word):
                    r += 1
                else:
                    o += 1

        if max(u, r, o) == u:
            return "uk"
        elif max(u, r, o) == r:
            return "ru"
        else:
            return None
    else:
        return lang


def correct_message(msg, lang='ru'):
    """
    Function corrects spelling mistakes
    msg: tuple (id, text) -- dictionary containing message info -- id and text (can be a word or a whole sentence)
    lang: str -- "ru", "uk" or "en"
    """
    # lang ru, uk, en
    speller = YandexSpeller(lang=lang)
    try:
        corr_word = speller.spelled(msg[1])
    except Exception:
        # log.error(msg)
        return (msg[0], "")
    return (msg[0], corr_word)
