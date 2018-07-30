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
        
    admin_list = [{display_name,url,minimum_rank_required(default = None),role_list(default = None)},]
    When processing the admin_list test:
         if minimum_rank_required is not None, the current user has a role with at least this rank
         OR
         if role_list is not None, the current user has a role (name) in the list
    """
    
    def __init__(self,db):
        self.db = db #A database connection. need it to instanciate tables
        self.admin_list = []
        
    def register(self,table,url,**kwargs):
        """Add an item to the admin_list"""
        display_name=kwargs.get('display_name',None)
        minimum_rank_required=kwargs.get('minimum_rank_required',None)
        role_list=kwargs.get('role_list',None)
        
        table_ref = table(self.db)
        if not display_name:
            display_name = table_ref.table_name.replace('_',' ').title()
            
        self.admin_list.append({'display_name':display_name,'url':url,'minimum_rank_required':minimum_rank_required,'role_list':role_list})
            