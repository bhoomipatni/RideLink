import os
import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from onelogin.saml2.auth import OneLogin_Saml2_Auth
from onelogin.saml2.metadata import OneLogin_Saml2_Metadata

load_dotenv()  # loads .env with SAML_PRIVATE_KEY

app = FastAPI()

# Enable CORS for SAML callback from IdP
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


def validate_sp_metadata(metadata_xml: str):
    """Handle python3-saml validator naming differences across versions."""
    if hasattr(OneLogin_Saml2_Metadata, "validate_metadata"):
        return OneLogin_Saml2_Metadata.validate_metadata(metadata_xml)
    if hasattr(OneLogin_Saml2_Metadata, "validateMetadata"):
        return OneLogin_Saml2_Metadata.validateMetadata(metadata_xml)
    return []

# Helper to convert FastAPI request to what python3-saml expects
async def prepare_flask_request(request: Request):
    # Determine the correct default port based on scheme
    default_port = 443 if request.url.scheme == 'https' else 80
    port = request.url.port or default_port
    
    # For POST requests, try to get form data
    post_data = {}
    if request.method == 'POST':
        try:
            post_data = dict(await request.form())
        except Exception as e:
            print(f"Error reading POST data: {e}")
    
    return {
        'http_host': request.url.hostname,
        'script_name': str(request.url.path),
        'server_port': port,
        'get_data': dict(request.query_params),
        'post_data': post_data,
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
    # Redirect the browser directly to the identity provider login.
    return RedirectResponse(url=auth.login())

@app.post("/callback")
async def callback(request: Request):
    print("=== CALLBACK RECEIVED ===")
    print(f"Method: {request.method}")
    print(f"URL: {request.url}")
    print(f"Headers: {dict(request.headers)}")
    
    req = await prepare_flask_request(request)
    print(f"Prepared request: {req}")
    
    auth = init_saml_auth(req)
    auth.process_response()
    errors = auth.get_errors()
    print(f"SAML Errors: {errors}")
    
    if errors:
        return {"errors": errors, "status": "error"}
    else:
        attributes = auth.get_attributes()
        name_id = auth.get_nameid()
        print(f"Login successful: {name_id}")
        return {"name_id": name_id, "attributes": attributes, "status": "success"}

@app.get("/metadata", response_class=HTMLResponse)
def metadata():
    metadata = OneLogin_Saml2_Metadata.builder(settings["sp"], None, True)
    errors = validate_sp_metadata(metadata)
    if len(errors) > 0:
        return {"errors": errors}
    return HTMLResponse(content=metadata, media_type="text/xml")


@app.get("/logout")
def logout():
    response = RedirectResponse(url="/")
    response.delete_cookie("session")
    return response