import { Gateway } from '../application/gateway.js';
import { buildOne } from './builds.js';
import { reconcileOne, recoverUnsubmitted } from './reconciliation.js';
import { retainAndRecover } from './retention.js';
import { logEvent, metrics } from '../security/observability.js';
export function startWorkers(gateway:Gateway):()=>Promise<void> {
  let stopping=false; const active=new Set<Promise<void>>();const timers:NodeJS.Timeout[]=[];
  function schedule(name:string,period:number,run:()=>Promise<unknown>):void {
    let busy=false;
    const timer=setInterval(()=>{
      if(stopping||busy)return;busy=true;
      const task=run().then(()=>{}).catch(()=>{metrics.increment('worker_failure');logEvent({event:'WORKER_FAILURE',component:name});})
        .finally(()=>{busy=false;active.delete(task);});active.add(task);
    },period);timers.push(timer);
  }
  for(let slot=0;slot<4;slot++)schedule('build',500,()=>buildOne(gateway));
  schedule('reconciliation',1000,()=>reconcileOne(gateway));
  schedule('unsubmitted-recovery',15000,()=>recoverUnsubmitted(gateway));
  schedule('retention',30000,()=>retainAndRecover(gateway));
  return async()=>{stopping=true;for(const timer of timers)clearInterval(timer);await Promise.allSettled(active);};
}
