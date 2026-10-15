import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';
export async function generateToAPIsImage(input) {
  const executable=process.env.TOAPIS_PYTHON || 'python';
  const file=fileURLToPath(new URL('./toapis_worker.py',import.meta.url));
  return await new Promise((resolve,reject)=>{
    const p=spawn(executable,[file],{env:process.env,stdio:['pipe','pipe','pipe'],windowsHide:true});
    let out='',error='';
    p.stdout.on('data',b=>{out+=b;if(out.length>48*1024*1024)p.kill();});
    p.stderr.on('data',b=>{error+=b;});
    p.on('error',reject);p.on('close',code=>{
      if(code!==0)return reject(new Error('ToAPIs worker failed; inspect private task state before retrying. '+error.slice(-500)));
      try{resolve(JSON.parse(out));}catch{reject(new Error('Invalid worker response'));}
    });
    p.stdin.end(JSON.stringify(input));
  });
}
