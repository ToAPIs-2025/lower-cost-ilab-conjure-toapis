"""CLI bridge: key comes only from the server environment; no POST retries."""
import argparse,base64,io,json,os,sys
from pathlib import Path
try:
    from .toapis_async import ToAPIsClient,build_request
    from .toapis_models import MODEL_ROUTES
except ImportError:
    from toapis_async import ToAPIsClient,build_request
    from toapis_models import MODEL_ROUTES
def run(job, key=None, base=None):
    model=job.get('model','gpt-image-2-vip')
    client=ToAPIsClient(key or os.environ.get('TOAPIS_API_KEY'),base or os.environ.get('TOAPIS_BASE_URL','https://toapis.com'))
    client.run_id=job.get('run_id','manual')
    try:rows=client._json('pricing?model='+model)
    except RuntimeError as exc:
        if model!='doubao-seedream-5-0-pro-global' or 'HTTP 503' not in str(exc):raise
        # Owner supplied pricing screenshot, 2026-10-15: 1K $0.045, 2K $0.09.
        # This is a quote, not a settled charge; never use it for another model.
        rows={'data':[{'id':model,'prices':[{'unit':'request','unit_price':'0.045','conditions':{'resolution':'1K'}}]}]}
    route=MODEL_ROUTES[model]
    matches=[]
    for item in rows.get('data',[]):
        if item['id']!=model:continue
        for p in item['prices']:
            c=p.get('conditions',{})
            if p.get('unit')!='request':continue
            if c.get('resolution','1K')!='1K':continue
            if c.get('quality',route['quality'])!=route['quality']:continue
            if c.get('n',1)!=1 or c.get('input_image_count',0)!=route['quoted_input_count']:continue
            matches.append(float(p['unit_price']))
    if not matches:raise ValueError('No exact current per-request quote for this model/tier')
    price=max(matches)
    if price>float(os.environ.get('TOAPIS_MAX_IMAGE_USD','0.10')):raise ValueError('Image quote exceeds cap')
    kwargs={'model':model,'prompt':job['prompt'],'size':job.get('size','1024x1024'),'n':1}
    handles=[open(x,'rb') for x in job.get('reference_files',[])]
    if handles:kwargs['image']=handles
    try:response=client.generate(**kwargs)
    finally:
        for h in handles:h.close()
    receipt=client.last_receipt
    return {'b64_json':response.data[0].b64_json,'url':response.data[0].url,'task_id':receipt['task_id'],'model':model,'quote_usd':price,'receipt':receipt,'actual_charge_usd':None}
if __name__=='__main__':
    job=json.load(sys.stdin)
    result=run(job)
    print(json.dumps(result,ensure_ascii=False))
