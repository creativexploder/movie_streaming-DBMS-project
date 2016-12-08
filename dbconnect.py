import MySQLdb

def connection():
	conn=MySQLdb.connect(host="localhost",
						user="<username>",
						passwd="<password>",
						db="<db-name>")
			
	c= conn.cursor()

	return c,conn