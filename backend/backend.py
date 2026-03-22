from fastapi import FastAPI, Depends, HTTPException, Request
from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import RedirectResponse

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key="LLOLLLLMOIEW")

# Configuration OAuth
config = Config()
oauth = OAuth(config)

# Configure Authentik comme fournisseur OAuth
oauth.register(
  name='authentik',
  client_id='UEPfa2K3rUacTcBr1hpSCjWwZMbG2z4xMogb6nyZ',
  client_secret='DoS5kLU8YY6f9umrFlh8L8HTErSG2YeWz2MjlTIE26aCFJfD6DfVKT3507Y4JWTybFf0YJEFLPktUS2wBGHFaNWnAHNdrYosTZT7UpA1Anai0f1kbkOurumpFHlWwyaP',
  authorize_url='https://authentik.dauphin.ovh/application/o/authorize/',
  authorize_params=None,
  access_token_url='https://authentik.dauphin.ovh/application/o/token/',
  refresh_token_url=None,
  client_kwargs=dict(
    scope='openid profile email',
    verify=False,
  ),
  server_metadata_url='https://authentik.dauphin.ovh/application/o/test-app/.well-known/openid-configuration',
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

ovh = alterserv.OVHApi()

[cloud] = ovh.cloud.ls()

for meta in cloud.provider.ls():
  @app.get(f"/{'/'.join(meta.path.split('.'))}")
  def get_resource(meta=meta, user: dict = Depends(user)):
    return [
      str(res)
      for res in meta.provider.ls()
    ]
  