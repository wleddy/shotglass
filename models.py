import sqlite3
from collections import namedtuple
from views.users.login import getPasswordHash
from views.utils import cleanRecordID

class Database:
    """Handle the basic database functions"""
    def __init__(self,filename=None):
        if filename == None:
            filename = 'app.db'
        
        self.filename = filename
        self.connection = None
    
    def connect(self):
        """Return a connection to the database"""
        self.connection = sqlite3.connect(self.filename)
        self.connection.row_factory = sqlite3.Row ## allows us to treat row as a dictionary
        self.connection.execute('PRAGMA foreign_keys = ON') #Turn on foreign key cascade support
        return self.connection
    
    def cursor(self):
        """Return a cursor to the current database"""
        if self.connection:
            return self.connection.cursor()
        else:
            raise sqlite3.DatabaseError('No connection opened to database')
    
    def close(self):
        if self.connection:
            self.connection.close()
            

class _Table:
    """Handle some basic interactions with the user table"""
    def __init__(self,db_connection):
        self.table_name = None
            
        self.db = db_connection
        self.order_by_col = 'id' #default orderby column(s)
    
    def create_table(self,definition=""):
        """The default table definition script. definition arg is a string of valid SQL"""
        
        # clean up the definition if needed
        definition = definition.rstrip()
        if definition != "":
            definition = ',' + definition.strip(',')
            
        sql = """CREATE TABLE IF NOT EXISTS '{}' (
            'id' INTEGER NOT NULL PRIMARY KEY{}
            )""".format(self.table_name,definition,)
        self.db.execute(sql)

    def init_table(self):
        """Base init method. Just create the table"""
        self.create_table()

    def get_column_names(self):
        """Return a list of column names for the table"""
        out = []
        cols = self.db.execute('PRAGMA table_info({})'.format(self.table_name)).fetchall()
        for col in cols:
            out.append(col[1])
            
        return out
        
    @property
    def data_tuple(self):
        """return a namedtuple for use with this table"""        
        return namedtuple('DataRow',"{}".format(",".join(self.get_column_names())))
        
    def rows_to_namedtuple(self,row_list):
        """return a list of namedtuples based on the list of Row objects provided"""
        out = None
        if row_list:
            out = [self.data_tuple._make(rec) for rec in row_list]
        return out
        
    def select(self,**kwargs):
        """
            perform a basic SELECT query returning a list namedtuples for all columns
            optional kwargs are:
                where: text to use in the where clause
                order_by: text to include in the order by clause
        """
        where = kwargs.get('where','1')
        order_by = kwargs.get('order_by',self.order_by_col)
        
        return self.rows_to_namedtuple(
            self.db.execute(
                'SELECT * FROM {} WHERE {} ORDER BY {}'.format(self.table_name,where,order_by,)
                ).fetchall()
            )
            
    def _single_row(self,rows):
        """Return the first element of list rows or else None"""        
        if rows:
            if len(rows) > 0:
                 return rows[0]
        return None
            
        # ++++++++++++++++++
    def get(self,id):
        """Return a list of a single namedtuple for the ID or None"""
        return self._single_row(self.select(where='id = {}'.format(cleanRecordID(id),)))
        
        
class Role(_Table):
    """Handle some basic interactions with the role table"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'role'
        self.order_by_col = 'name'
        
    def create_table(self):
        sql = """
            'name' TEXT UNIQUE NOT NULL,
            'description' TEXT,
            'rank' INTEGER DEFAULT 0 """
        super().create_table(sql)
        
    def init_table(self):
        """Create the table and initialize data"""
        self.create_table()
        
        #Try to get a value from the table and create records if none
        rec = self.db.execute('select * from {}'.format(self.table_name)).fetchone()
        if not rec:
            roles = [
                (None,'super','Super User',1000),
                (None,'admin','Admin User',500),
                (None,'user','Normal user',1),
            ]
            self.db.executemany("insert into {} values (?,?,?,?)".format(self.table_name),roles)
            self.db.commit()


class UserRole(_Table):
    """Handle some basic interactions with the user_role table"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'user_role'
    
    def create_table(self):
        sql = """
            'user_id' INTEGER,
            'role_id' INTEGER,
            FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
            FOREIGN KEY (role_id) REFERENCES role(id) ON DELETE CASCADE """
        super().create_table(sql)
                
        
class User(_Table):
    """Handle some basic interactions with the user table"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'user'
            
    def get(self,id,include_inactive=False,**kwargs):
        """Return a list with a single namedtuple for the user with this id
            A keyword argument for include_inactive controls filtering
            of active users only
        """
        include_inactive = kwargs.get('include_inactive',include_inactive)
        where = 'id = {} {}'.format(cleanRecordID(id),('' if include_inactive else 'and active = 1'))

        return self._single_row(self.rows_to_namedtuple(
                self.db.execute('SELECT * FROM {} WHERE {} ORDER BY id'.format(self.table_name,where)).fetchall()
                ))

    def get_by_username_or_email(self,nameoremail):
        """Return a single namedtuple obj or none based on the username or email"""
        
        sql = "select * from {} where (username = ? or email = ?) and active = 1 order by id".format(self.table_name)
        
        return self._single_row(
                self.rows_to_namedtuple(
                    self.db.execute(
                    sql,(nameoremail,nameoremail,)
                    ).fetchall()
                )
            )
    
    def get_roles(self,userID,**kwargs):
        """Return a list of the role namedtuple objects for the user's roles"""
        
        order_by = kwargs.get('order_by','rank desc, name')
        sql = """select * from role where id in
                (select role_id from user_role where user_id = ?) order by {}
                """.format(order_by)
                
        return  Role(self.db).rows_to_namedtuple(self.db.execute(sql,(cleanRecordID(userID),)).fetchall())
    
    def create_table(self):
        sql = """
            'first_name' TEXT,
            'last_name' TEXT,
            'email' TEXT UNIQUE,
            'phone' TEXT,
            'address' TEXT,
            'address2' TEXT,
            'city' TEXT,
            'state' TEXT,
            'zip' TEXT,
            'username' TEXT UNIQUE,
            'password' TEXT,
            'active' INTEGER DEFAULT 1,
            'last_login' DATETIME 
            """
        super().create_table(sql)
        
    def init_table(self):
        """Create the table in the db and optionally add some initial data"""
        self.create_table()
        
        #Try to get a value from the table and create a record if none
        rec = self.db.execute('select * from {}'.format(self.table_name)).fetchone()
        if not rec:
            sql = """insert into {}
                (first_name,last_name,username,password)
                values
                ('Admin','User','admin','{}')
            """.format(self.table_name,getPasswordHash('password'))
            self.db.execute(sql)
            #self.db.commit()
            
            # Give the user super powers
            rec = self.get(1)
            userID = rec['id']
            rec = self.db.execute('select id from role where name = "super"').fetchone()
            roleID = rec['id']
            self.db.execute('insert into user_role (user_id,role_id) values (?,?)',(userID,roleID))
            self.db.commit()

        
def init_db(db):
    Role(db).init_table()
    UserRole(db).init_table()
    User(db).init_table()
    db.close()
    