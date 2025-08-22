import pyautogui as pu
import wikipedia as wk
import webbrowser
from langdetect import detect


t = str(pu.prompt("search:"))


try:
    language = detect(t)

    if language == 'fa':
        wk.set_lang("fa")

    elif language == 'en':
        wk.set_lang("en")

    else:
        wk.set_lang("en")
except:

    wk.set_lang("en")

search_results = wk.search(t)


if search_results:

    webbrowser.open(wk.page(search_results[0]).url)


else:

    pu.alert("not.")