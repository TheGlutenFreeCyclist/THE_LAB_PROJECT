"""NO FLASK shim: QA static/module bootstrap only, never ship in production."""
import contextlib
import importlib.util
import logging
import os
import sys
import types
from pathlib import Path
from jinja2 import Environment

class TestConfig(dict):
    def update(self, *args, **kw):
        return super().update(*args, **kw)
class FakeFlask:
    def __init__(self, *args, **kw):
        self.jinja_env=Environment(autoescape=True)
        self.jinja_env.globals.update(url_for=lambda *a,**kw:"/preview", request=StubRequest(), session={})
        self.logger=logging.getLogger('qa_flask_shim')
        self.config=TestConfig()
        self.view_functions={}
    def route(self, rule,*a,**kw):
        def decorator(f):
            self.view_functions[f.__name__]=f
            return f
        return decorator
    def before_request(self,f):return f
    def after_request(self,f):return f
    def errorhandler(self,*a,**kw): return lambda f:f
    def context_processor(self,f):return f
    def add_template_filter(self,fn,name=None):
        self.jinja_env.filters[name or fn.__name__]=fn
    def run(self,*a,**kw):raise AssertionError('NEVER_RUN_LIVE_SERVER')
class StubRequest:
    endpoint=None; form={}; headers={}; args={}; method='GET'; cookies={}; is_json=False
    def __getattr__(self,key):return None

def load(path):
    fakeflask=types.ModuleType('flask')
    fakeflask.Flask=FakeFlask
    fakeflask.session={}
    fakeflask.request=StubRequest()
    fakeflask.redirect=lambda *a,**kw:None
    fakeflask.url_for=lambda *a,**kw:'/'
    fakeflask.render_template_string=lambda s,**kw:Environment(autoescape=True).from_string(s).render(**kw)
    fakeflask.Response=lambda *a,**kw:None
    fakeflask.jsonify=lambda *a,**kw:None
    fakeflask.abort=lambda *a,**kw:None
    fakeflask.g=types.SimpleNamespace()
    fakeflask.has_request_context=lambda:False
    fake_werkzeug=types.ModuleType('werkzeug')
    fake_werkzeug.__path__=[]
    fake_security=types.ModuleType('werkzeug.security')
    fake_security.generate_password_hash=lambda a,*args:'NOT_A_REAL_HASH'
    fake_security.check_password_hash=lambda a,b:False
    fake_security.__package__='werkzeug'
    old={k:sys.modules.get(k) for k in ('flask','werkzeug','werkzeug.security')}
    try:
        sys.modules.update({'flask':fakeflask,'werkzeug':fake_werkzeug,'werkzeug.security':fake_security})
        os.environ['PRODUCT_SECURITY_STRICT']='0'
        spec=importlib.util.spec_from_file_location('nova_qa_app',str(path))
        mod=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        for k,v in old.items():
            if v is None:sys.modules.pop(k,None)
            else:sys.modules[k]=v

if __name__=='__main__':
    obj=load(Path(sys.argv[1]))
    print('BOOTSTRAP_OK',obj.APP_VERSION,len(obj.HOME_PAGE),len(obj.app.view_functions))
