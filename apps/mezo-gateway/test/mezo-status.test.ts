import assert from 'node:assert/strict';
import { once } from 'node:events';
import { createServer } from 'node:http';
import test from 'node:test';
import { Contracts } from '../src/adapters/contracts.js';
import type { Ledger } from '../src/adapters/postgres.js';
import { Gateway } from '../src/application/gateway.js';
import type { ArtifactStore, PaymentPort, ReportService } from '../src/ports/index.js';
import { createApp } from '../src/routes/app.js';

for (const [state,reason] of [['BUILD_FAILED','MEZO_SOURCE_UNAVAILABLE'],['REJECTED','MEZO_DEX_INVALID_EVIDENCE']] as const) {
  test(`public request polling preserves ${reason}`, async () => {
    const id='11111111-1111-4111-8111-111111111111';
    const contracts=await Contracts.load(new URL('../../dist/contracts/',import.meta.url));
    const ledger={async rateLimit(){},async request(){return {id,state,reason};}} as unknown as Ledger;
    const gateway=new Gateway(ledger,{} as ReportService,{} as ArtifactStore,{} as PaymentPort,contracts,{payTo:null,sourceMode:'live-public'});
    const server=createServer(createApp(gateway,new Set()));
    server.listen(0,'127.0.0.1');await once(server,'listening');
    const address=server.address();assert(address&&typeof address==='object');
    try {
      const response=await fetch(`http://127.0.0.1:${address.port}/v1/report-requests/${id}`,{
        headers:{authorization:`Bearer ${Buffer.alloc(32).toString('base64url')}`},
      });
      assert.equal(response.status,200);
      const body=await response.json() as {state:string;reason:string};
      assert.equal(body.state,state);assert.equal(body.reason,reason);
    }finally{server.close();await once(server,'close');}
  });
}
