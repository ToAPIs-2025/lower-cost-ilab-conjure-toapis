export function generateToAPIsImage(input:Record<string,unknown>):Promise<{b64_json:string,url:string,task_id:string,model:string,quote_usd:number}>;
export function generateToAPIsVideo(input:Record<string,unknown>):Promise<{videoUrl:string,provider:string,upstreamId:string,durationSec:number}>;
