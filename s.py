import pyautogui as pu
import wikipedia as wk

t = str(pu.prompt("search :"))

search = wk.search(t)

pu.alert(search)