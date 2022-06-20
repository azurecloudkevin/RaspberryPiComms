import mysql
from mysql.connector import connect, Error

verify_query = """
SELECT *
FROM hostdata
WHERE
    hostName = %s
"""

server_query = """
SELECT hostIPAddress
FROM hostdata
WHERE role = "server"
ORDER BY hostLastCheckin DESC
LIMIT 1
"""

initial_insert = """
INSERT into hostdata 
VALUES(%s, %s, %s, %s, %s)
ON DUPLICATE KEY UPDATE hostIPAddress=%s, hostLastCheckin=%s
"""

update_query = """
SELECT hostIPAddress
FROM hostdata
WHERE
    hostID = "64227"
"""

checkin_insert = """
UPDATE hostdata
SET hostLastCheckin = CURRENT_TIMESTAMP(), hostIPAddress = %s
WHERE hostName = %s
"""

resolve_alarm = """
UPDATE alarms 
SET ack_hostname = %s, alarm_ack_timestamp = CURRENT_TIMESTAMP()
WHERE alarm_index = %s
"""

insert_alarm = """
INSERT INTO alarms 
(alarm_index, alarm_trigger_timestamp, alarm_description) 
VALUES (%s, CURRENT_TIMESTAMP(), 'alarm')
"""

class mysqlconnect:
    def __init__(self, hostname, username, passwd, dbname):
        self.host = hostname
        self.user = username
        self.pw = passwd
        self.db = dbname


    def run_query_arguments(self, query, arguments):
        queryresult=[]
        try:
            with connect(
                host=self.host,
                user=self.user,
                password=self.pw,
                database=self.db
            ) as connection:
                with connection.cursor(buffered = True) as cursor:
                    for result in cursor.execute(query, arguments, multi=True):
                        if result.with_rows:
                            queryresult = cursor.fetchall()
                    connection.commit()

        except Error as e:
            print(e)

        return queryresult

    def run_query_no_arguments(self, query):
        queryresult=[]

        try:
            with connect(
                host=self.host,
                user=self.user,
                password=self.pw,
                database=self.db
            ) as connection:
                with connection.cursor(buffered = True) as cursor:
                    for result in cursor.execute(query, multi=True):
                        if result.with_rows:
                            queryresult = cursor.fetchall()
                    connection.commit()

        except Error as e:
            print(e)

        return queryresult
                
    def server_ip_query(self):
        results = self.run_query_no_arguments(server_query)
        return results[0]

    def initial_insert_query(self, hostID, hostname, ipaddress, checkintime, role):
        arguments = [hostID, hostname, ipaddress, checkintime, role, ipaddress, checkintime]
        self.run_query_arguments(initial_insert, arguments)

    def checkin(self, hostip, hostname):
        arguments = [hostip, hostname]
        self.run_query_arguments(checkin_insert, arguments)

    def add_alarm(self, index):
        arguments = [index]
        self.run_query_arguments(insert_alarm, arguments)

    def resolve_alarm_status(self, hostname, alarmID):
        arguments = [hostname, alarmID]
        self.run_query_arguments(resolve_alarm, arguments)
    