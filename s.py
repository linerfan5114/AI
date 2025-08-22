import pyautogui as pu
import wikipedia as wk
import webbrowser

t = str(pu.prompt("Search:"))
search = wk.search(t)

if search:
    webbrowser.open(f"https://en.wikipedia.org/wiki/{search[0]}")
else:
    pu.alert("No results found.")