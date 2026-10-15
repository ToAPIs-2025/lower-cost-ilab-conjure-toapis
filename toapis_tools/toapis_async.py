"""MIT-licensed ToAPIs async adapter for the upstream CLI's images interface."""
from pathlib import Path
from types import SimpleNamespace
from urllib.parse import urlparse,quote
import base64,hashlib,json,math,os,re,sys,time,urllib.request,urllib.error,uuid
try:
    from .toapis_models import MODEL_ROUTES
except ImportError:
    from toapis_models import MODEL_ROUTES

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None

def normalize_origin(base):
    u=urlparse(base)
    if u.scheme!='https' or u.hostname not in ('toapis.cn','toapis.com') or u.username or u.password or u.port or u.query or u.fragment or u.path.rstrip('/') not in ('','/v1'):
        raise ValueError('Use https://toapis.cn or https://toapis.com, optionally ending in /v1')
    return 'https://'+u.hostname

def build_request(kwargs,resolution='1K'):
    k=dict(kwargs);model=k.pop('model',None)
    if model not in MODEL_ROUTES:raise ValueError('Model is not in the inspected ToAPIs generation contract')
    if k.pop('n',1)!=1:raise ValueError('ToAPIs demo requires n=1')
    if resolution not in ('1K','2K','4K'):raise ValueError('Resolution must be 1K, 2K or 4K')
    if k.pop('mask',None) is not None:raise ValueError('Mask/inpainting is not supported by this adapter')
    if k.pop('input_fidelity',None) is not None:raise ValueError('input_fidelity is not supported')
    if k.pop('background',None) not in (None,'auto','opaque'):raise ValueError('Transparent output is not supported')
    if k.pop('output_format',None) not in (None,'png'):raise ValueError('This demo saves PNG only')
    if k.pop('output_compression',None) is not None or k.pop('user',None) is not None:raise ValueError('Compression/user are not mapped')
    # Upstream defaults moderation=low. It has no equivalent knob in this route.
    k.pop('moderation',None)
    size=k.pop('size','1024x1024');m=re.fullmatch(r'(\d+)x(\d+)',size)
    if not m:raise ValueError('Use an explicit CLI size, e.g. 1024x1024; auto is not mapped')
    w,h=map(int,m.groups())
    if min(w,h)<=0 or max(w,h)>3840 or w%16 or h%16:raise ValueError('Invalid size; use positive 16px multiples up to 3840')
    gcd=math.gcd(w,h);ratio=f'{w//gcd}:{h//gcd}'
    if ratio not in ('1:1','16:9','9:16','4:3','3:4','3:2','2:3','21:9'):raise ValueError('Aspect ratio is not mapped')
    route=MODEL_ROUTES[model]
    if resolution!='1K':raise ValueError('This fork enables tested 1K routes only')
    body={'model':model,'prompt':k.pop('prompt'),'n':1,'size':ratio}
    body['resolution']=resolution if route['resolution_field'] in ('top','both') else None
    if route['resolution_field']=='metadata':
        body.pop('resolution');body['metadata']={'resolution':resolution}
    elif route['resolution_field']=='both':body['metadata']={'resolution':resolution}
    quality=k.pop('quality',route['quality'])
    if quality!=route['quality']:raise ValueError('Quality must match the inspected model tier')
    if model in ('gpt-image-2-vip','gpt-image-2.5-flare'):body['quality']=quality
    references=k.pop('image',None) or []
    if references and model!='gpt-image-2-vip':raise ValueError('Reference edits outside VIP are not validated by this fork')
    if k:raise ValueError('Unmapped parameters: '+','.join(sorted(k)))
    return body,references

class ToAPIsClient:
    def __init__(self,key,base='https://toapis.cn',resolution='1K',state_dir=None):
        if not key:raise ValueError('TOAPIS_API_KEY is required')
        self.key=key;self.origin=normalize_origin(base);self.resolution=resolution
        self.state=Path(state_dir or os.environ.get('TOAPIS_STATE_DIR','.toapis-state'));self.state.mkdir(parents=True,exist_ok=True)
        self.http=urllib.request.build_opener(NoRedirect);self.images=self;self.last_receipt=None
    def _json(self,path,body=None,content_type='application/json'):
        payload=json.dumps(body).encode() if isinstance(body,dict) else body
        req=urllib.request.Request(self.origin+'/v1/'+path,data=payload,headers={'Authorization':'Bearer '+self.key,'Content-Type':content_type},method='POST' if body is not None else 'GET')
        try:
            with self.http.open(req,timeout=60) as r:return json.load(r)
        except urllib.error.HTTPError as e:raise RuntimeError('ToAPIs HTTP '+str(e.code)+' at '+path) from None
    def _asset(self,url):
        u=urlparse(url)
        if u.scheme!='https' or u.username or u.password:raise RuntimeError('Unsafe result URL')
        # CDN denies Python's default User-Agent (Cloudflare 1010 observed).
        # Result requests carry no API key, even when hosted on another origin.
        req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Accept':'image/*'})
        with self.http.open(req,timeout=120) as r:return r.read()
    def generate(self,**kwargs):return self._run(kwargs)
    def edit(self,**kwargs):return self._run(kwargs)
    def _run(self,kwargs):
        body,handles=build_request(kwargs,self.resolution);refs=[]
        for handle in handles:
            raw=handle.read();name=Path(handle.name).name;suffix=Path(name).suffix.lower()
            mime={'.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.webp':'image/webp'}.get(suffix)
            if not mime:raise ValueError('References must be PNG/JPEG/WebP')
            refs.append((raw,mime))
        identity={'origin':self.origin,'request':body,'references':[hashlib.sha256(r).hexdigest() for r,_ in refs],'keyFingerprint':hashlib.sha256(self.key.encode()).hexdigest(),'run':getattr(self,'run_id',os.environ.get('TOAPIS_RUN_ID','default'))}
        fingerprint=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest();receipt_file=self.state/(fingerprint+'.json')
        receipt=json.loads(receipt_file.read_text(encoding='utf-8')) if receipt_file.exists() else None
        if receipt and not receipt.get('task_id'):raise RuntimeError('Prior generation submission is uncertain. Check Task Logs before submitting again.')
        def save():receipt_file.write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf-8')
        if not receipt:
            urls=[]
            for raw,mime in refs:
                boundary='ToAPIs'+uuid.uuid4().hex;extension={'image/png':'png','image/jpeg':'jpg','image/webp':'webp'}[mime]
                data=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="reference.{extension}"\r\nContent-Type: {mime}\r\n\r\n'.encode()+raw+f'\r\n--{boundary}--\r\n'.encode())
                urls.append(self._json('uploads/images',data,'multipart/form-data; boundary='+boundary)['data']['url'])
            request={**body,**({'reference_images':urls} if urls else {})}
            receipt={'task_id':None,'state':'submitting','request':{**body,**({'reference_images':['<uploaded URL omitted>']*len(urls)} if urls else {})},'observations':[],'billing':None}
            try:
                with receipt_file.open('x',encoding='utf-8') as first_receipt:json.dump(receipt,first_receipt,ensure_ascii=False,indent=2)
            except FileExistsError:raise RuntimeError('A concurrent submission already owns this task receipt. Query it before trying again.') from None
            try:task=self._json('images/generations',request)
            except Exception as e:raise RuntimeError('Submission response unavailable; receipt retained. Reconcile Task Logs before a new POST.') from None
            receipt.update(task_id=task.get('id'),state='submitted');save()
            if not receipt['task_id']:raise RuntimeError('No task ID; do not automatically resubmit')
            print(json.dumps({'event':'submitted','task_id':receipt['task_id'],'model':body['model']},ensure_ascii=False),file=sys.stderr,flush=True)
        task_id=receipt['task_id'];started=time.monotonic()
        while time.monotonic()-started<600:
            task=self._json('images/generations/'+quote(task_id,safe=''));status=task.get('status')
            if task.get('model') and task['model']!=body['model']:raise RuntimeError('Returned task model does not match request')
            receipt['returned_model']=task.get('model')
            receipt['observations'].append({'status':status,'billing':task.get('billing')});receipt.update(state=status,billing=task.get('billing'));save();self.last_receipt=receipt
            if status=='completed':
                receipt['result_url']=task['result']['data'][0]['url'];save()
                raw=self._asset(receipt['result_url'])
                return SimpleNamespace(data=[SimpleNamespace(b64_json=base64.b64encode(raw).decode(),url=receipt['result_url'])])
            if status in ('failed','cancelled','expired'):raise RuntimeError('Task '+task_id+' ended '+str(status)+'; no resubmission')
            time.sleep(8)
        raise RuntimeError('Timed out; keep and query task '+task_id)
