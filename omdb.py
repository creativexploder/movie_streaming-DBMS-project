import requests
from dbconnect import connection
import sqlite3
import MySQLdb
import urllib
import os


mname= raw_input("Enter movie")	
r = requests.get("http://www.omdbapi.com/",params ={"t" : mname, "plot" : "full", "r" : "json" })
for key in r.json().keys():
	if key == "Year" and len(r.json()["Year"])==9:
		ear = r	.json()["Year"][:4]+"-"+r.json()["Year"][-4:]
		print str(key), " : ", r.json()["Year"][:4]+"-"+r.json()["Year"][-4:]
		continue
	elif key == "Year":
		ear = r.json()["Year"][:4]+"-"
		print str(key), " : ", r.json()["Year"][:4]+"-"
		continue
# print str(key), " : ", str((r.json()[key]).encode('unicode_escape'))
	
imdbrating = r.json()["imdbRating"]
runtime = r.json()["Runtime"]
posterimg = r.json()["Poster"]
actors = (r.json()["Actors"].encode('unicode_escape')).split(',')
genre = (r.json()["Genre"]).split(',')
plot = r.json()["Plot"].encode('unicode_escape')
r_date= r.json()["Released"]
poster= r.json()["Poster"]

print "ear: ", ear
print "Rate: ",imdbrating
print "Runtime: ",runtime
print "Poster: ",posterimg
print "Actors: ",actors
print "Genre: ",genre
print "Plot: ",plot
print "Released", r_date

fullfilename = os.path.join("static/poster_img", mname+".jpg")
urllib.urlretrieve(poster,fullfilename)

c,conn=connection()	
for act in actors:
	y=int(c.execute("SELECT actor_id from actor WHERE actor_name=(%s)",[(act.strip())]))
	if int(y)==0:
		print "inserting actor"
		c.execute("INSERT INTO actor (actor_name) VALUES (%s)",[(act.strip())])
		conn.commit()
		print "actor inserted"
	for gn in genre:
		x=int(c.execute("SELECT g_id from genre WHERE gname=(%s)",[(gn.strip())]))
		if int(x)==0:
			print "inserting value"
			c.execute("INSERT INTO genre (gname) VALUES (%s)",[(gn.strip())])
			conn.commit()
			print "value inserted"
	
		data= c.execute("SELECT * FROM genre WHERE gname= (%s)",[(gn.strip())])
		data =c.fetchone()[0]
		datax = c.execute("SELECT * FROM actor WHERE actor_name= (%s)",[(act.strip())])
		datax =c.fetchone()[0]
		#print data
		c.execute("INSERT INTO movies (plot, mname,g_id,act_id,rate,year,runtime,r_date,poster_image) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",((plot),(mname),(data),(datax),(imdbrating),(ear),(runtime),(r_date),(mname+".jpg")))
		conn.commit()
	


