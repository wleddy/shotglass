from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from instance.site_settings import DATABASE_URI, MAIL_DEFAULT_ADDR, MAIL_PASSWORD
from flask_security.utils import hash_password

engine = create_engine(DATABASE_URI, \
                       convert_unicode=True)
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
                                         
Base = declarative_base()
Base.query = db_session.query_property()

def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    import models
    Base.metadata.create_all(bind=engine)
    db_session.commit()
    
    # Create a default admin user and role
    role = models.Role()
    role.name = "superuser"
    db_session.add(role)
    user = models.User()
    user.email = MAIL_DEFAULT_ADDR
    user.password = hash_password(MAIL_PASSWORD)
    db_session.add(user)
    db_session.commit()
    userRole = models.RolesUsers()
    userRole.role_id = role.id
    userRole.user_id = user.id
    db_session.add(userRole)
    db_session.commit()