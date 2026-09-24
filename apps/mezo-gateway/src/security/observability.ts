const allowedMetrics=['http_request','http_error','payment_required','payment_verified','payment_settled','payment_unknown',
  'authorization_duplicate','delivery_failure','artifact_integrity_failure','build_complete','build_rejected',
  'worker_failure','reconciliation_complete'] as const;
type Metric=typeof allowedMetrics[number];
class Metrics {
  private readonly counters=new Map<Metric,number>();
  private readonly durations=new Map<'build'|'reconciliation',{count:number;sum:number}>();
  private ready=0;
  readiness(value:boolean):void {this.ready=value?1:0;}
  increment(name:Metric):void {this.counters.set(name,(this.counters.get(name)??0)+1);}
  observe(name:'build'|'reconciliation',seconds:number):void {
    if(!Number.isFinite(seconds)||seconds<0)return;
    const value=this.durations.get(name)??{count:0,sum:0};value.count++;value.sum+=seconds;this.durations.set(name,value);
  }
  render():string {
    const counters=allowedMetrics.map(name=>`# TYPE liqvera_${name}_total counter\nliqvera_${name}_total ${this.counters.get(name)??0}`);
    const durations=[...this.durations].map(([name,value])=>`# TYPE liqvera_${name}_seconds summary\nliqvera_${name}_seconds_count ${value.count}\nliqvera_${name}_seconds_sum ${value.sum}`);
    return [...counters,...durations,`# TYPE liqvera_payment_ready gauge\nliqvera_payment_ready ${this.ready}`].join('\n')+'\n';
  }
}
export const metrics=new Metrics();
interface Event { event:string; request_id?:string; quote_id?:string; payment_attempt_id?:string; code?:string; component?:string; status?:number; duration_ms?:number }
export function logEvent(event:Event):void {
  // Allowlist projection. Never serialize Error objects, URLs, bodies, wallets,
  // capabilities, cookies, authorization identity or PAYMENT-* values.
  const output:Record<string,unknown>={time:new Date().toISOString()};
  for(const key of ['event','request_id','quote_id','payment_attempt_id','code','component','status','duration_ms'] as const) {
    if(event[key]!==undefined)output[key]=event[key];
  }
  process.stdout.write(JSON.stringify(output)+'\n');
}
