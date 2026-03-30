from fastapi import FastAPI, Depends, HTTPException, Request
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse

import os

app = FastAPI()

SESSION_KEY = os.environ["SESSION_KEY"]

OAUTH2_CLIENT_ID = os.environ["OAUTH2_CLIENT_ID"]
OAUTH2_CLIENT_SECRET = os.environ["OAUTH2_CLIENT_SECRET"]

AUTHENTIK_URL = os.environ["AUTHENTIK_URL"]
AUTHENTIK_APP = os.environ["AUTHENTIK_APP"]

app.add_middleware(SessionMiddleware, secret_key=SESSION_KEY)

# Configuration OAuth
config = Config()
oauth = OAuth(config)

# Configure Authentik comme fournisseur OAuth
oauth.register(
  name='authentik',
  client_id=OAUTH2_CLIENT_ID,
  client_secret=OAUTH2_CLIENT_SECRET,
  authorize_url=f'{AUTHENTIK_URL}/application/o/authorize/',
  authorize_params=None,
  access_token_url=f'{AUTHENTIK_URL}/application/o/token/',
  refresh_token_url=None,
  client_kwargs=dict(
    scope='openid profile email',
    verify=False,
  ),
  server_metadata_url=f'{AUTHENTIK_URL}/application/o/{AUTHENTIK_APP}/.well-known/openid-configuration',
)

@app.get('/login')
async def login(request: Request, to: str = "/"):
  request.session["to"] = to
  redirect_uri = request.url_for('auth')
  return await oauth.authentik.authorize_redirect(request, redirect_uri)

@app.get('/logout')
async def logout(request: Request, to: str = "/"):
  response = RedirectResponse(url=to)
  request.session.pop("access_token")
  return response

@app.get('/auth/callback')
async def auth(request: Request):
  try:
    token = await oauth.authentik.authorize_access_token(request)
    print(token)

    # Stocke le token complet dans un cookie JSON
    response = RedirectResponse(url=request.session["to"])
    request.session["access_token"] = token["access_token"]
    return response
  except Exception as e:
    raise HTTPException(status_code=400, detail=str(e))

async def access_token(request : Request):
  try:
    auth_header = request.headers.get("Authorization")
    
    if auth_header and auth_header.startswith("Bearer"):
      return auth_header.split()[1]
    
    return request.session["access_token"]
  except Exception as e:
    raise HTTPException(
      status_code=401,
      detail=f"Token not found",
    )

async def user(access_token: str = Depends(access_token)):
  try:
    user = await oauth.authentik.userinfo(
      token=dict(
        access_token=access_token,
        token_type="Bearer"
      ),
    )
    return user
  except Exception as e:
    raise HTTPException(
      status_code=401,
      detail=f"Invalid Token : {str(e)}",
    )

@app.get('/me')
async def get_me(user: dict = Depends(user)):
  return user

import alterserv

ovh = alterserv.OVHApi.build()

[project] = ovh.cloud.project.ls()


from alterserv.core import *
from types import SimpleNamespace

class ObjectVisitor:
  def __init__(self, obj, path=[], parents=[]):
    self.obj = obj
    self.path = path
    self.parents = parents

  @property
  def children_parents(self):
    return [
      *self.parents,
      self.obj.__class__.__name__,
    ]

  @property
  def children(self):
    if self.obj.__class__.__name__ in self.parents:
      return []
    else:
      ret = []
      if isinstance(self.obj, Resource):
        ret = ret + [
          self.__class__(getattr(self.obj, field.name), [*self.path, field.name], self.children_parents)
          for field in self.obj.__fields__.values()
        ]
        if isinstance(self.obj, Provider):
          ret = ret + [
            self.__class__(self.obj.Resource, [*self.path, "provide"], self.children_parents)
          ]
        return ret
      elif isinstance(self.obj, Atomic):
        return []
      elif type(self.obj).__name__ in ["str", "int", "list", "dict", "type"]: # TODO remove
        return []
      else:
        raise TypeError(f"{self.obj.__class__.__name__} not expected to be visited")


class MyVisitor(ObjectVisitor):
  def visit_Resource(self):
    ret = []
    if isinstance(self.obj, alterserv.Resource):
      print("Resource", self.path, self.obj)
    if isinstance(self.obj, alterserv.Provider):
      print("Provider", self.path, self.obj)
      ret.append(SimpleNamespace(
        path=self.path,
        provider=self.obj,
      ))
    return ret

  def ls(self):
    ret = []
    ret = ret + self.visit_Resource()
    for child in self.children:
      ret = ret + child.ls()
    return ret

for meta in MyVisitor(project).ls():
  @app.get('/'.join(["", *meta.path]))
  def get_resource(meta=meta, user: dict = Depends(user)):
    return [
      res.config.to_dict()
      for res in meta.provider.ls()
    ]
