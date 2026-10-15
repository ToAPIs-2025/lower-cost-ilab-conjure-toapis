"""Explicit ToAPIs host adapter for iLab's existing OpenAI Images profile."""
import base64,io,os,sys,tempfile
from pathlib import Path
from PIL import Image
from codex_image.generation.types import GeneratedAsset,GenerationResult
def execute_toapis(plan):
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'toapis_tools'))
    from toapis_worker import run
    command=plan.command
    if command.mask_image or command.reference_files:raise ValueError('Mask/file attachments are not mapped')
    params=dict(command.parameters)
    if plan.protocol_request.repeat_count!=1:raise ValueError('Only a single request is supported')
    if set(params)-{'size','n','background'}:raise ValueError('Unmapped generation options')
    if params.get('n',1)!=1 or params.get('background','opaque') not in ('opaque','auto'):raise ValueError('Only one opaque image is supported')
    # The local patch intentionally exposes only the verified square 1K preset.
    if params.get('size','1024x1024')!='1024x1024':raise ValueError('Only square 1K preset is verified')
    refs=[]
    try:
        for item in command.image_inputs:
            if not item.data_url.startswith('data:image/png;base64,'):raise ValueError('References must be local PNG data URLs')
            f=tempfile.NamedTemporaryFile(suffix='.png',delete=False);f.write(base64.b64decode(item.data_url.split(',',1)[1],validate=True));f.close();refs.append(f.name)
        result=run({'model':plan.binding.remote_model_id,'prompt':command.prompt,'run_id':os.environ.get('TOAPIS_RUN_ID','manual'),'reference_files':refs},key=plan.provider.api_key,base=plan.provider.base_url)
    finally:
        for path in refs:Path(path).unlink(missing_ok=True)
    raw=base64.b64decode(result.pop('b64_json')); image=Image.open(io.BytesIO(raw)); image.load()
    fmt=image.format or 'PNG';mime=Image.MIME.get(fmt,'image/png')
    return GenerationResult(assets=(GeneratedAsset(raw,mime,image.width,image.height,metadata={'model':result['model']}),),provider_metadata={'toapis':result})
