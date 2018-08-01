###########################################
## admin.py
## Control what tables a user may access as an
## administrator.
###########################################

class Admin():
    """Register tables to be administered then check a user's access permissions
    
    Instanciate as:
        admin = Admin(g.db)
        
    Register an admin table:
        Admin.register(TableObj,url,[,display_name=None[,minimum_rank_required=None[,role_list=None]]])
        
    admin_list = [{table,display_name,url,minimum_rank_required(default = 99999999),role_list(default = [])},]
    
    When processing the admin_list test:
         that the current user has a role with at least this rank
         OR
         that the current user has a role (name) in the list
    """
    
    def __init__(self,db):
        self.db = db #A database connection. need it to instanciate tables
        self.admin_list = []
        
    def register(self,table,url,**kwargs):
        """Add an item to the admin_list"""
        display_name=kwargs.get('display_name',None)
        minimum_rank_required=kwargs.get('minimum_rank_required',99999999) #No one can access without a qualifiying role
        role_list=kwargs.get('role_list',[])
        
        table_ref = table(self.db)
        if not display_name:
            display_name = table_ref.display_name
            
        self.admin_list.append({'table':table,'display_name':display_name,'url':url,'minimum_rank_required':minimum_rank_required,'role_list':role_list})
           
    def has_access(self,user_name,display_name=None):
        """Test to see if the user represented by user name has access to ANY admin items
        If the display_name is specified, only check to see if user has access to that table"""
        from users.models import User
        if len(self.admin_list) > 0:
            user = User(self.db)
            rec = user.get(user_name)
            if rec:
                roles = user.get_roles(rec.id)
                temp_list = self.admin_list
                if display_name:
                    temp_list = [x for x in temp_list if x['display_name'] == display_name]
                if temp_list:
                    if roles:
                        for role in roles:
                            for list_item in temp_list:
                                if role.name in list_item['role_list']:
                                    return True
                                if list_item['minimum_rank_required'] <= role.rank:
                                    return True
        return False