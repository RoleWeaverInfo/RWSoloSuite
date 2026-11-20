"""Explicit, read-only model checks for locally stored provider credentials."""
import json
import re
import urllib.error
import urllib.request


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        return None  # Never forward a credential to another URL.


def check_models(credentials,provider,models):
    if provider not in ('openai','gemini'):raise ValueError('Choose OpenAI or Gemini')
    if not isinstance(models,list) or not 1<=len(models)<=2 or any(not isinstance(m,str) or not re.fullmatch(r'[A-Za-z0-9._-]{1,100}',m) for m in models):
        raise ValueError('Choose one or two valid model IDs')
    key=credentials.get(provider)
    if not key:raise ValueError('Save a key for this provider before checking model access')
    base='https://api.openai.com/v1/models/' if provider=='openai' else 'https://generativelanguage.googleapis.com/v1beta/models/'
    headers={'Authorization':'Bearer '+key} if provider=='openai' else {'x-goog-api-key':key}
    opener=urllib.request.build_opener(NoRedirect())
    checked=[]
    for model in dict.fromkeys(models):
        request=urllib.request.Request(base+model,headers=headers,method='GET')
        try:
            with opener.open(request,timeout=15) as response:
                data=json.loads(response.read(100_000))
        except urllib.error.HTTPError as exc:
            # Do not echo provider error bodies; they can contain credential text.
            message={401:'The provider rejected the saved key. Create or copy a valid key and save it again.',
                     403:'Access was denied. Check key permissions, account eligibility and model access.',
                     404:'This model was not found or is unavailable to your account. Choose another model.',
                     429:'The provider limited this check. Check your account limits and try again later.'}.get(exc.code,'The provider could not complete the model check. Try again later.')
            raise ValueError(model+': '+message) from None
        except (OSError,ValueError):
            raise ValueError('Could not check model access. Check your internet connection and try again.') from None
        if not isinstance(data,dict) or data.get('id' if provider=='openai' else 'name')!=(model if provider=='openai' else 'models/'+model):
            raise ValueError('The provider returned unexpected model information')
        if provider=='gemini' and 'generateContent' not in (data.get('supportedGenerationMethods') or []):
            raise ValueError(model+' does not support the text-generation endpoint used by Studio')
        checked.append(model)
    return {'provider':provider,'models':checked,'message':'Model information is accessible with this key. No text or images were generated. This does not verify generation permissions, available credits, free-tier eligibility or remaining quota.'}
