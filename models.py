import sqlite3
from namedlist import namedlist #Like namedtuples but mutable
from views.utils import cleanRecordID
from flask import g
from views.users.password import getPasswordHash


class Database:
    """Handle the basic database functions"""
    def __init__(self,filename):        
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
        self.defaults = {}
        
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
        return namedlist('DataRow',"{}".format(",".join(self.get_column_names())),default=None)
        
    def delete(self,id):
        """Delete a single row with this id.
        Return True or False"""
        
        #import pdb;pdb.set_trace()
        row = self.get(id,include_inactive = True)
        if row:
            self.db.execute('delete from {} where id = ?'.format(self.table_name),(id,))
            return True
               
        return False
        
    def rows_to_namedlist(self,row_list):
        """return a list of namedlists based on the list of Row objects provided"""
        out = None
        if row_list and len(row_list)>0 and row_list[0] != None:
            out = [self.data_tuple(*rec) for rec in row_list]
        return out
        
    def new(self,set_defaults=True):
        """return an 'empty' namedlist for the table. Normally set the default values for the table"""
        rec = self.data_tuple()
        if set_defaults:
            self.set_defaults(rec)
        return rec
        
    def save(self,row_data,**kwargs):
        """Save the data in row_data to the db.
        row_data is a named list
        
        If row_data.id == None, insert, else update an existing record
        
        trim_strings=False in kwargs will write to db as received. else strip strings first
        
        The data is re read from the db after save and row_data is updated in place so the calling methods has 
        an update version of the data.
        
        return the id value of the effected row
        
        """
        
        def get_params(row_data):
            params = ()
            for x in range(1,len(row_data)):
                params += (row_data[x],)
            return params
            
        strip_strings = kwargs.get('strip_strings',True) # Strip by default
        if strip_strings == True:
            for x in range(1,len(row_data)):
                if type(row_data[x]) is str:
                    row_data[x] = row_data[x].strip()
                    
        insert_new = False
        #generate the data param tuple
        
        if (row_data.id == None):
            insert_new = True
            self.set_defaults(row_data)
            params = get_params(row_data)
            
            sql = 'insert into {} ({}) values ({})'.format(
                self.table_name,
                ",".join([row_data._fields[x] for x in range(1,len(row_data))]),
                ','.join(["?" for x in range(1,len(row_data))])
            )
        else:
            params = get_params(row_data)
            
            sql = 'update {} set {} where id = ?'.format(
                self.table_name,
                ",".join(["{} = ?".format(row_data._fields[x]) for x in range(1,len(row_data))])
            )
            params +=(row_data.id,)
                    
        # need to use a raw cursor so we can retrieve the last row inserted
        cursor = self.db.cursor()
        cursor.execute(sql,(params))
                
        if insert_new:
            row_id = cursor.lastrowid
        else:
            row_id = row_data.id
            
        # Don't use the self.get() method here because there may be constraints as in User
        temp_row = cursor.execute('select * from {} where id = {}'.format(self.table_name,row_id)).fetchone()
        
        if temp_row == None:
            raise TypeError
            #pass # Should really do something with this bit of infomation
        else:
            for x in range(1,len(row_data)):
                row_data[x] = temp_row[x]
            
        row_data.id = row_id
                    
        return row_id
        
    def set_defaults(self,row_data):
        """When creating a new record, set the defaults for this table"""
        if row_data.id == None and len(self.defaults) > 0:
            row_dict = row_data._asdict()
            for key, value in self.defaults.items():
                if row_dict[key] == None:
                    row_data._update({key:value})
        
    def _select_sql(self,**kwargs):
        """Return the sql text that will be used by select or select_one
        optional kwargs are:
            where: text to use in the where clause
            order_by: text to include in the order by clause
        """
        where = kwargs.get('where','1')
        order_by = kwargs.get('order_by',self.order_by_col)
        sql = 'SELECT * FROM {} WHERE {} ORDER BY {}'.format(self.table_name,where,order_by,)
        return sql
        
    def select(self,**kwargs):
        """
            perform a basic SELECT query returning a list namedlists for all columns
        """
        recs = self.db.execute(self._select_sql(**kwargs)).fetchall()
        if recs:
            return self.rows_to_namedlist(recs)
        return None
        
    def select_one(self,**kwargs):
        """a version of select method that returns a single named list object or None"""
        rows = self.rows_to_namedlist(
            [self.db.execute(
                self._select_sql(**kwargs)
                ).fetchone()]
            )
        return self._single_row(rows)
                
    def select_raw(self,sql,params=''):
        """Returns a list of named list objects based on the sql text with optional string substitutions"""
        return self.rows_to_namedlist(self.db.execute(sql,params).fetchall())
        
    def select_one_raw(self,sql,params=''):
        """Return a single namedlist for sql select statement"""
        return self._single_row(self.select_raw(sql,params))
            
    def get(self,id,**kwargs):
        """Return a list of a single namedlist for the ID or None"""
        return self._single_row(self.select(where='id = {}'.format(cleanRecordID(id),)))
        
    def _single_row(self,rows):
        """Return the first element of list rows or else None"""        
        if rows:
            if len(rows) > 0:
                 return rows[0]
        return None
        
    def update(self,rec,form,save=False):
        """Update the rec with the matching elements in form
        rec is a record namedlist 
        form is an InmutableMultiDict or a dictionary object
        
        The id element is never updated. Before calling this method be sure that any elements
        in form that have names matching names in rec contain the values you want.
        
        Optionally can save the rec (but not committed) after update
        """
        for key,value in rec._asdict().items():
            if key != 'id' and key in form:
                rec._update([(key,form[key])])
                
        if save:
            self.save(rec)
            
        
class Role(_Table):
    """Handle some basic interactions with the role table"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'role'
        self.order_by_col = 'name'
        self.defaults = {'rank':0,}
        
    def create_table(self):
        """Define and create the role tablel"""
        
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
        """Define and create the user_role tablel"""
        
        sql = """
            'user_id' INTEGER NOT NULL,
            'role_id' INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
            FOREIGN KEY (role_id) REFERENCES role(id) ON DELETE CASCADE """
        super().create_table(sql)
                
        
class User(_Table):
    """Handle some basic interactions with the user table"""
    def __init__(self,db_connection):
        super().__init__(db_connection)
        self.table_name = 'user'
        self.order_by = 'id'
        self.defaults = {'active':1,}
        
    def _active_only_clause(self,include_inactive=False,**kwargs):
        """Return a clause for the select statement to include active only or empty string"""
        include_inactive = kwargs.get('include_inactive',include_inactive)
        if include_inactive:
            return ""
        
        return 'and active = 1'
        
    def delete(self,rec_id):
        """Delete a single user record as indicated
        'id' may be an integer or a string"""
        
        rec = self.get(rec_id,include_inactive=True)
        if rec:
            return super().delete(rec.id)
            
        return False
        
    def get(self,id,**kwargs):
        """Return a single namedlist for the user with this id
            A keyword argument for include_inactive controls filtering
            of active users only
        """
        #if the 'id' is a string, try to find the user by username or email
        if type(id) is str:
            return self.get_by_username_or_email(id,**kwargs)
            
        include_inactive = kwargs.get('include_inactive',False)
        where = 'id = {} {}'.format(cleanRecordID(id),self._active_only_clause(include_inactive))

        return self.select_one(where=where)

    def get_by_username_or_email(self,nameoremail,**kwargs):
        """Return a single namedlist obj or none based on the username or email"""

        include_inactive = kwargs.get('include_inactive',False)

        sql = "select * from {} where (username = ? or lower(email) = lower(?)) {} order by id".format(self.table_name,self._active_only_clause(include_inactive))
        
        return self._single_row(self.select_raw(sql,(nameoremail.strip(),nameoremail.strip())))
    
    def get_roles(self,userID,**kwargs):
        """Return a list of the role namedlist objects for the user's roles"""
        
        order_by = kwargs.get('order_by','rank desc, name')
        sql = """select * from role where id in
                (select role_id from user_role where user_id = ?) order by {}
                """.format(order_by)
                
        return  Role(self.db).rows_to_namedlist(self.db.execute(sql,(cleanRecordID(userID),)).fetchall())
                
    def select(self,**kwargs):
        """Limit selection to active user only unless 'include_inactive' is true in kwargs"""
        where = '{} {}'.format(kwargs.get('where','1'),self._active_only_clause(kwargs.get('include_inactive',False)))
            
        order_by = kwargs.get('order_by',self.order_by_col)
        
        return super().select(where=where,order_by=order_by)
        
    def update_last_access(self,user_id,no_commit=False):
        """Update the 'last_access field with the current datetime. Default is for record to be committed"""
        if type(user_id) is int:
            self.db.execute('update user set last_access = datetime() where id = ?',(user_id,))
            if not no_commit:
                self.db.commit()
        
    def create_table(self):
        """Define and create the user tablel"""
        
        sql = """
            'first_name' TEXT,
            'last_name' TEXT,
            'email' TEXT UNIQUE COLLATE NOCASE,
            'phone' TEXT,
            'address' TEXT,
            'address2' TEXT,
            'city' TEXT,
            'state' TEXT,
            'zip' TEXT,
            'username' TEXT UNIQUE,
            'password' TEXT,
            'active' INTEGER DEFAULT 1,
            'last_access' DATETIME 
            """
        super().create_table(sql)
        
    def init_table(self):
        """add some initial data"""

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
            userID = rec.id
            rec = Role(self.db).select_one(where='name = "super"')
            roleID = rec.id
            self.db.execute('insert into user_role (user_id,role_id) values (?,?)',(userID,roleID))
            self.db.commit()

        
def init_db(db):
    """Create a intial user record."""
    Role(db).init_table()
    UserRole(db).init_table()
    User(db).init_table()
    