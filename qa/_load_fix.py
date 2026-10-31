"""Offline-only R196.9.99: Jinja composition + projection; NO Flask/DB/Intervals."""
import sys, types, importlib.util, copy, json, ast
from pathlib import Path
from jinja2 import Environment, StrictUndefined
root=Path(__file__).resolve().parents[1]
F=types.ModuleType('flask')
class FakeFlask:
    def __init__(self,*args,**kwargs):
        self.config={};self.secret_key=None;self.view_functions={}
        self.jinja_env=Environment(autoescape=True)
        self.logger=types.SimpleNamespace(info=lambda *x:None,warning=lambda *x:None,exception=lambda *x:None)
    def __getattr__(self,key):
        if key in ('route','before_request','after_request','errorhandler','context_processor','template_filter'):
            return lambda *a,**k: lambda f:f
        if key=='add_template_filter':return lambda *a,**k:None
        if key in ('run',):return lambda *a,**k:None
        raise AttributeError(key)
F.Flask=FakeFlask
for v in ['session','request','g']:
    setattr(F,v,{})
for v in ['redirect','url_for','render_template_string','Response','jsonify','abort','has_request_context']:
    setattr(F,v,lambda *a,**k:None)
W=types.ModuleType('werkzeug'); S=types.ModuleType('werkzeug.security')
S.generate_password_hash=lambda s,**k:'hash'; S.check_password_hash=lambda a,b:True
sys.modules['flask']=F;sys.modules['werkzeug']=W;sys.modules['werkzeug.security']=S
p=root/'the_lab_app.py'
spec=importlib.util.spec_from_file_location('the_lab_r196999_offline',p)
mod=importlib.util.module_from_spec(spec)
sys.modules[spec.name]=mod
try:
    spec.loader.exec_module(mod)
except AssertionError as exc:
    t=mod.HOME_PAGE
    print("FAIL",exc,"articles",t.count("</article>"),"fuel",t.count("v23-session-fuel"))
    for n in [a for a in range(len(t)) if t.startswith("</article>",a)][:16]:
        print(repr(t[n-90:n+160]))
    raise

print('LOADED',mod.APP_VERSION)
