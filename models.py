from database import Base
from flask_security import UserMixin, RoleMixin
from flask_security.utils import hash_password
from sqlalchemy import create_engine
from sqlalchemy.orm import relationship, backref
from sqlalchemy import Boolean, DateTime, Column, Integer, \
                       String, ForeignKey


class RolesUsers(Base):
    __tablename__ = 'roles_users'
    id = Column(Integer(), primary_key=True)
    user_id = Column('user_id', Integer(), ForeignKey('user.id'))
    role_id = Column('role_id', Integer(), ForeignKey('role.id'))
    
    def __init__(self,role_id,user_id):
        self.role_id = role_id
        self.user_id = user_id
        

class Role(Base, RoleMixin):
    __tablename__ = 'role'
    id = Column(Integer(), primary_key=True)
    name = Column(String(80), unique=True)
    description = Column(String(255))
    
    def __repr__(self):
        return self.name
        
    def __init__(self,name):
        self.name = name
        
    
class User(Base, UserMixin):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True)
    username = Column(String(255))
    password = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    last_login_at = Column(DateTime())
    current_login_at = Column(DateTime())
    last_login_ip = Column(String(100))
    current_login_ip = Column(String(100))
    login_count = Column(Integer)
    active = Column(Boolean(),default = True)
    confirmed_at = Column(DateTime())
    roles = relationship('Role', secondary='roles_users',
                         backref=backref('users', lazy='dynamic'))

    def __repr__(self):
        full_name = 'none known'
        if self.first_name != None and self.last_name != None:
            full_name = self.first_name + " " + self.last_name
        elif self.username != None:
            full_name = self.username
        elif self.email != None:
            full_name = self.email
            
        return full_name
        
    def __init__(self, email, password):
        self.email = email
        self.password = hash_password(password)

