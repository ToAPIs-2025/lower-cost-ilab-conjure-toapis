"""Generate one case only with --live. Dry-run makes no network requests."""
import argparse,base64,json,sys
from pathlib import Path
from toapis_tools.toapis_async import build_request
from toapis_tools.toapis_worker import run
p=argparse.ArgumentParser();p.add_argument('--model',default='gpt-image-2-vip');p.add_argument('--prompt',required=True);p.add_argument('--run-id',default='manual');p.add_argument('--output',default='result.png');p.add_argument('--live',action='store_true');a=p.parse_args()
job={'model':a.model,'prompt':a.prompt,'run_id':a.run_id}
if not a.live:
 print(json.dumps({'dry_run':True,'request':build_request({'model':a.model,'prompt':a.prompt,'size':'1024x1024'})[0],'paid_calls':0}));raise SystemExit(0)
result=run(job);raw=base64.b64decode(result.pop('b64_json'))
from PIL import Image
import io
image=Image.open(io.BytesIO(raw));image.load();fmt=image.format or 'PNG'
target=Path(a.output);target.parent.mkdir(parents=True,exist_ok=True)
extension={'JPEG':'.jpg','PNG':'.png','WEBP':'.webp'}.get(fmt,'.bin')
original=target.with_name(target.stem+'.original'+extension);original.write_bytes(raw)
# Always save an actual PNG at the presentation path, never a JPEG disguised as PNG.
if target.suffix.lower()!='.png':target=target.with_suffix('.png')
image.save(target,format='PNG')
result.update(actual_dimensions=[image.width,image.height],original_format=fmt,original_file=original.name,presentation_file=target.name)
result.pop('url',None);result.get('receipt',{}).pop('result_url',None)
target.with_suffix('.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('Saved original bytes with correct extension, a PNG presentation copy and receipt.')
