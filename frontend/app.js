import * as fs from 'fs';
import * as dotenv from 'dotenv';

dotenv.config();  //loads.env

const settings = JSON.parse(fs.readFileSync("config/settings.json", 'utf8'));

//private key from environment
settings.sp.privateKey = process.env.SAML_PRIVATE_KEY;
