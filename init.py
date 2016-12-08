from flask import Flask, render_template, flash, request, url_for, redirect, session
import sqlite3
from wtforms import Form, BooleanField, TextField, PasswordField, validators
from wtforms.fields.html5 import EmailField
from dbconnect import connection
from functools import wraps
from passlib.hash import sha256_crypt
from MySQLdb import escape_string as escape
import gc
app=Flask(__name__)
recent=[]
movie=[]
@app.route('/')
def homepage():	
	return render_template("homepage2.html")

@app.route('/dashboard/')
def dashboard():
	recent={}
	mrecent=[]
	precent=[]
	c,conn=connection()
	rece=c.execute("select distinct(mname),plot from movies order by STR_TO_DATE(r_date,'%e %b %Y') desc LIMIT 10")
	for i in range(0,int(rece)):
		x=c.fetchone()
		recent[x[0]]=x[1]
		#mrecent=x[0]
		#precent=x[1]
	return render_template("dashboard.html",recent=recent)

@app.errorhandler(404)	
def page_not_found(e):
	return render_template("404.html")

def login_required(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash("You need to login first")
			return redirect(url_for('login'))
		
	return wrap	
	

@app.route('/search', methods=["GET","POST"])
@login_required
def search():
	srch={}
	a_id=[]
	m_id={}
	movi={}
	c,conn=connection()
	if request.method == "POST":	
		asrc=c.execute("SELECT actor_id FROM actor WHERE actor_name LIKE (%s)", ["%"+(request.form['search'])+"%"])
		for i in range(0,int(asrc)):
			a_id.append(c.fetchone()[0])
		for val in a_id:
			mn=c.execute("SELECT distinct(mname) from movies where act_id=(%s)",[(val)])
			for i in range(0,mn):
				srch.setdefault(val,[]).append(c.fetchone()[0])
		for aid,mid in srch.items():
			ji=c.execute("SELECT actor_name from actor where actor_id= (%s)",[(aid)])
			movi.setdefault(c.fetchone()[0],[]).extend(mid)	
		#movie search
		msrc=c.execute("SELECT distinct(mname),plot from movies where mname LIKE (%s)", ["%"+(request.form['search'])+"%"])
		for i in range(0,int(msrc)):
			x=c.fetchone()
			m_id[x[0]]=x[1]
		return render_template("search.html",mlist=movi,m_id=m_id)
	
	
@app.route('/logout/')
@login_required
def logout():
	session.clear()
	#flash("You are logged out")
	gc.collect
	return redirect(url_for('homepage'))
	
	
@app.route('/login/', methods=["GET","POST"])
def login():
	error=''
	try:
		c,conn=connection()
		if request.method == "POST": 
			
			data= c.execute("SELECT * FROM entries WHERE username= (%s)",[escape(request.form['username'])])
			data =c.fetchone()[2]
			
			#if int(data) == 0:
			#	error = "Invalid Username/Password.  Try again!"
			
			if sha256_crypt.verify(request.form['password'], data):
				session['logged_in'] = True
				session['username'] = request.form['username']
				flash("You are now logged in!")
				return redirect(url_for('dashboard'))
			else:
				error= "Invalid Username/Password.  Try again!"
				
		gc.collect()
		return render_template("login.html",error=error)
				
	except Exception as e:
		#flash (e)
		error= "Invalid Username/Password.  Try again!"
		return render_template("login.html", error=error)
	
class RegistrationForm(Form):
	username = TextField('Username',[validators.Length(min=4,max=50)])
	email = EmailField('Email Address',[validators.Length(min=15,max=50),validators.DataRequired(), validators.Email()])
	password = PasswordField('Password',[validators.Required(),validators.EqualTo('confirm', message="Passwords must match") ])
	card=TextField('Credit/Debit Card Number',[validators.Length(min=0,max=16)])
	confirm = PasswordField('Confirm Password')
	accept_tos = BooleanField('I accept the <a href="/terms-of-service/">Terms of Service</a> and <a href="/privacy">Privacy Statement</a>',[validators.Required()])
	
@app.route('/signup/', methods=["GET","POST"])
def signup():
	try:
		form= RegistrationForm(request.form)
		if request.method == "POST" and form.validate():
			username = form.username.data
			email = form.email.data
			card=form.card.data
			password =sha256_crypt.encrypt((str(form.password.data)))
			c,conn=connection()
			u= c.execute("SELECT * FROM entries WHERE username = (%s)",[(escape(username))])
			
			if int(u)>0:
				flash("Username already taken, Choose another one")
				return render_template("signup.html", form=form)
			else:
				c.execute("INSERT INTO entries(username, password, email,card_no) VALUES (%s, %s, %s, %s)",(escape(username),escape(password),escape(email),escape(card)))
				
				conn.commit()
				flash("Thanks for Registering")
				c.close()
				conn.close()
				gc.collect()
				
				session['logged_in'] = True
				session['username'] = username
				
				return redirect(url_for('dashboard'))
		
		return render_template("signup.html",form=form)	
		
	except Exception as e:
		return(str(e)) 	
	
	#return render_template("signup.html")
@app.route('/<name>', methods=["GET","POST"])
@app.route('/dashboard/<name>', methods=["GET","POST"])
@app.route('/profile/<name>', methods=["GET","POST"])
@login_required
def movie_page(name):
	c,conn=connection()
	movie=[]
	purchase=""
	p=None
	buyp=None
	met=request.method
	name=name.replace("-"," ")
	#name
	mn=c.execute("SELECT distinct(mname) from movies where mname=(%s)",[(name)])		
	movie_name=c.fetchone()[0]	
	movie.append(movie_name)

	#plot
	mp=c.execute("SELECT distinct(plot) from movies where mname=(%s)",[(name)])
	movie_plot=c.fetchone()[0]
	movie.append(movie_plot)

	#genre
	mge=[]
	movie_genre=[]
	mg=c.execute("SELECT distinct(g_id) from movies where mname=(%s)",[(name)])		
	for i in range(0,mg):
		mge.append(int(c.fetchone()[0]))
	for gid in mge:
		mgenre=c.execute("select gname from genre where g_id=(%s)",[(gid)])
		movie_genre.append(c.fetchone()[0])
	movie.append(movie_genre)

	#actors
	mac=[]
	movie_actor=[]
	ma=c.execute("SELECT distinct(act_id) from movies where mname=(%s)",[(name)])		
	for i in range(0,ma):
		mac.append(int(c.fetchone()[0]))
	for aid in mac:
		mactor=c.execute("select actor_name from actor where actor_id=(%s)",[(aid)])
		movie_actor.append(c.fetchone()[0])
	movie.append(movie_actor)

	#Imdbrate
	mr=c.execute("SELECT distinct(rate) from movies where mname=(%s)",[(name)])		
	movie_rate=c.fetchone()[0]	
	movie.append(str(movie_rate))

	#runtime
	mrt=c.execute("SELECT distinct(runtime) from movies where mname=(%s)",[(name)])		
	movie_run=c.fetchone()[0]	
	movie.append(movie_run)

	#Released Date
	mrd=c.execute("SELECT distinct(r_date) from movies where mname=(%s)",[(name)])		
	movie_rdate=c.fetchone()[0]	
	movie.append(movie_rdate)
	
	#poster_image
	i=c.execute("SELECT distinct(poster_image) from movies where mname=(%s)",[(name)])
	img=str(c.fetchone()[0])
	movie_img=url_for('static',filename='poster_img/' + img)
	movie.append(movie_img)
	
	"""if request.method == "POST":
		if request.form["submit"] == "rent":
			return render_template('movie_page.html')
		elif request.form["submit"] == "buy":
			return render_template('movie_page.html',movie=movie,buyp=int(bb_check),p=p)
		else:
			return render_template('movie_page.html',p="KUCH NAI KIYA")"""
	if request.method == "GET":
		uname=str(session['username'])
		uiid=c.execute("SELECT uid FROM entries where username=(%s)",[(uname)])
		user=int(c.fetchone()[0])
		mr=c.execute("SELECT mid FROM movies where mname=(%s) LIMIT 1",[(name)])
		mrname=int(c.fetchone()[0])
		cd=c.execute("SELECT curdate()")
		curr_date=c.fetchone()[0]
		r_check=c.execute("SELECT uid,mid from rent_subscription where uid=(%s) and mid=(%s)",((user),(mrname)))
		if int(r_check)>0:
			p=1
		else:
			p=None
		b_check=c.execute("SELECT uid,mid from buy_subscription where uid=(%s) and mid=(%s)",((user),(mrname)))
		if int(b_check)>0:
			buyp=1
			p=1
		else:
			buyp=None	
		return render_template('movie_page.html',movie=movie,p=p,buyp=buyp)
	
	#return render_template("movie_page.html",movie=movie,name=name)
	
@app.route('/profile/')
def profile():
	c,conn=connection()
	lst=[]
	blst=[]
	bmlst=[]
	#Rented_movies
	fuid=c.execute("SELECT uid from entries where username=(%s)",[(session['username'])])
	fuid=int(c.fetchone()[0])
	ruid=c.execute("SELECT mid from rent_subscription where uid=(%s)",[(fuid)])
	for i in range(0,int(ruid)):
		lst.append(int(c.fetchone()[0]))

	mst=[]
	for moid in lst:
		ids=c.execute("SELECT mname from movies where mid=(%s)",[(moid)])	
		mst.append(str(c.fetchone()[0]))
		
	#Movies_bought
	bfuid=c.execute("SELECT uid from entries where username=(%s)",[(session['username'])])
	bfuid=int(c.fetchone()[0])
	bruid=c.execute("SELECT mid from buy_subscription where uid=(%s)",[(fuid)])
	for i in range(0,int(bruid)):
		blst.append(int(c.fetchone()[0]))

	bmst=[]
	for moid in blst:
		ids=c.execute("SELECT mname from movies where mid=(%s)",[(moid)])	
		bmst.append(str(c.fetchone()[0]))

	return render_template('profile.html',mst=mst,bmst=bmst)
	
@app.route('/<name>/checkout',methods=["GET","POST"])
def checkout(name):
	name=name.replace("-"," ")
	c,conn=connection()
	if request.form["submit"] == "rent":
		
		pm=c.execute("SELECT distinct(mname),poster_image from movies where mname= (%s)",[(name)])
		xpm=c.fetchone()
		xcard=c.execute("SELECT card_no from entries where username= (%s)",[(session['username'])])
		xc=c.fetchone()[0]
		type="Rent"
		met=request.method
		return render_template('checkout.html',xpm=xpm,type=type,met=met,xc=xc)	
	elif request.form["submit"] == "buy":
		pm=c.execute("SELECT distinct(mname),poster_image from movies where mname= (%s)",[(name)])
		xpm=c.fetchone()
		xcard=c.execute("SELECT card_no from entries where username= (%s)",[(session['username'])])
		xc=c.fetchone()[0]
		type="Buy"
		return render_template('checkout.html',xpm=xpm,type=type,xc=xc)
		
@app.route('/<name>/<type>')
def payment(name,type):
	mname=name
	name=name.replace("-"," ")
	c,conn=connection()
	if type=='rent':
		uname=str(session['username'])
		uiid=c.execute("SELECT uid FROM entries where username=(%s)",[(uname)])
		user=int(c.fetchone()[0])
		mr=c.execute("SELECT mid FROM movies where mname=(%s) LIMIT 1",[(name)])
		mrname=int(c.fetchone()[0])
		cd=c.execute("SELECT card_no FROM entries where username=(%s)",[(uname)])
		cdd=int(c.fetchone()[0])
		cd=c.execute("SELECT curdate()")
		curr_date=c.fetchone()[0]
		datetime=c.execute("SELECT now()")
		dt=c.fetchone()[0]
		rented=c.execute("INSERT into rent_subscription (uid,mid,r_date) VALUES (%s, %s, %s)",((user),(mrname),(curr_date)))
		add_bill=c.execute("INSERT into bill (uid,card_number,mid,ptype) VALUES (%s, %s, %s, %s)",((user),(cdd),(mrname),(type)))
		add_his=c.execute("INSERT into purchase_history (uid,mname,p_date,type) VALUES (%s, %s, %s, %s)",((user),(name),(dt),(type)))
		conn.commit()
		return redirect(url_for('movie_page',name=mname))
	
	if type=="buy":
		uname=str(session['username'])
		uiid=c.execute("SELECT uid FROM entries where username=(%s)",[(uname)])
		user=int(c.fetchone()[0])
		mr=c.execute("SELECT mid FROM movies where mname=(%s) LIMIT 1",[(name)])
		mrname=int(c.fetchone()[0])
		cd=c.execute("SELECT card_no FROM entries where username=(%s)",[(uname)])
		cdd=int(c.fetchone()[0])
		cd=c.execute("SELECT curdate()")
		curr_date=c.fetchone()[0]
		datetime=c.execute("SELECT now()")
		dt=c.fetchone()[0]
		buy=c.execute("INSERT into buy_subscription (uid,mid,b_date) VALUES (%s, %s, %s)",((user),(mrname),(curr_date)))
		del_rent=c.execute("DELETE from rent_subscription where uid=(%s) and mid=(%s)",((user),(mrname)))
		add_bill=c.execute("INSERT into bill (uid,card_number,mid,ptype) VALUES (%s, %s, %s, %s)",((user),(cdd),(mrname),(type)))
		add_his=c.execute("INSERT into purchase_history (uid,mname,p_date,type) VALUES (%s, %s, %s, %s)",((user),(name),(dt),(type)))
		conn.commit()
		return redirect(url_for('movie_page',name=mname))
		
@app.route('/bills/')
def bills():
	l=[]
	c,conn=connection()
	uname=str(session['username'])
	uiid=c.execute("SELECT uid FROM entries where username=(%s)",[(uname)])
	user=int(c.fetchone()[0])
	bl=c.execute("SELECT card_number,mid,ptype from bill where uid=(%s)",[(user)])
	for i in range(0,int(bl)):
		l.append(c.fetchone())
	ml=[]
	for i in range(0,len(l)):
		m=c.execute("SELECT mname from movies where mid=(%s)",[(l[i][1])])
		ml.append(c.fetchone()[0])	
	a=len(l)	
	return render_template('bills.html',l=l,ml=ml,a=a)	
	
@app.route('/history/')
def history():
	c,conn=connection()
	uname=str(session['username'])
	uiid=c.execute("SELECT uid FROM entries where username=(%s)",[(uname)])
	user=int(c.fetchone()[0])
	hi=c.execute("SELECT mname,p_date,type from purchase_history where uid=(%s)",[(user)])
	his=[]
	for i in range(0,int(hi)):
		his.append(c.fetchone())
	a=len(his)	
	return render_template('history.html',his=his,a=a)
if __name__== "__main__":
	app.secret_key= 'super secret_key'
	app.run(debug=True)
	
	
	