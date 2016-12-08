import requests

text=raw_input("Enter movie: ")

r = requests.get("http://www.omdbapi.com/",params ={"t" : text, "plot" : "full", "r" : "json" })
for key in r.json().keys():
	if key == "Year" and len(r.json()["Year"])==9:
		print str(key), " : ", r.json()["Year"][:4]+"-"+r.json()["Year"][-4:]
		continue
	elif key == "Year":
		print str(key), " : ", r.json()["Year"][:4]+"-"
		continue
  
	print str(key), " : ", str((r.json()[key]).encode('unicode_escape'))