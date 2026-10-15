import sys,json,base64,os
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from codex_image.providers.contracts import *
from codex_image.generation.types import *
from codex_image.providers.openai import OpenAIImagesAdapter
job=json.load(sys.stdin)
binding=ProviderModelBinding('toapis-'+job['model'],'toapis','gpt-image-2',job['model'],'openai_images','openai_images',frozenset({'generate'}))
provider=ProviderConnection('toapis','ToAPIs','https://toapis.com/v1',os.environ['TOAPIS_API_KEY'],1,(binding,))
model=ModelManifest('gpt-image-2','gpt','GPT Image','gpt-image-2',1,frozenset({'generate'}),(),InputConstraints(1,False,False))
command=GenerationCommand('generate','gpt-image-2','toapis',job['prompt'],{'size':'1024x1024','n':1})
plan=ExecutionPlan(command,model,provider,binding,ProtocolRequest('POST','/images/generations','application/json',{}))
generation=OpenAIImagesAdapter().execute(plan)
result=dict(generation.provider_metadata['toapis']);result['b64_json']=base64.b64encode(generation.assets[0].image_bytes).decode()
print(json.dumps(result))
