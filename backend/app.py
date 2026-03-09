import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from onelogin.saml2.auth import OneLogin_Saml2_Auth

load_dotenv()  # loads .env with SAML_PRIVATE_KEY

app = FastAPI()

# Load settings.json
with open("config/settings.json") as f:
    settings = json.load(f)

# Inject private key from .env
settings["sp"]["privateKey"] = os.environ["SAML_PRIVATE_KEY"].replace("\\n", "\n")


# Load x509cert
with open("keys/server.crt") as f:
    settings["sp"]["x509cert"] = f.read()

# Initialize SAML auth (helper)
def init_saml_auth(req):
    return OneLogin_Saml2_Auth(req, settings)

# Helper to convert FastAPI request to what python3-saml expects
async def prepare_flask_request(request: Request):
    return {
        'http_host': request.url.hostname,
        'script_name': str(request.url.path),
        'server_port': request.url.port or 80,
        'get_data': dict(request.query_params),
        'post_data': dict(await request.form()) if request.method == 'POST' else {},
        'https': 'on' if request.url.scheme == 'https' else 'off'
    }


# --- Routes ---

@app.get("/", response_class=HTMLResponse)
def home():
    return "<a href='/login'>Login with RPI</a>"

@app.get("/login")
async def login(request: Request):
    req = await prepare_flask_request(request)
    auth = init_saml_auth(req)
    # Redirect to IdP login
    return {"login_url": auth.login()}

@app.post("/callback")
async def callback(request: Request):
    req = await prepare_flask_request(request)
    auth = init_saml_auth(req)
    auth.process_response()
    errors = auth.get_errors()
    if errors:
        return {"errors": errors}
    else:
        attributes = auth.get_attributes()
        name_id = auth.get_nameid()
        return {"name_id": name_id, "attributes": attributes}

@app.get("/metadata", response_class=HTMLResponse)
def metadata():
    from onelogin.saml2.metadata import OneLogin_Saml2_Metadata
    metadata = OneLogin_Saml2_Metadata.builder(settings["sp"], None, True)
    errors = OneLogin_Saml2_Metadata.validate_metadata(metadata)
    if len(errors) > 0:
        return {"errors": errors}
    return HTMLResponse(content=metadata, media_type="text/xml")
