import assert from "node:assert/strict";
import test from "node:test";
import { walletChoices } from "../src/wallet-discovery.ts";
import { readFile } from "node:fs/promises";

const provider=label=>({label,async request(){return null;}});
test("EIP-6963 providers are deterministic and legacy is only fallback",()=>{
  const a=provider("a"),b=provider("b"),legacy=provider("legacy");
  const store={getProviders:()=>[
    {info:{uuid:"b",name:"Zulu",icon:"",rdns:"z.example"},provider:b},
    {info:{uuid:"a",name:"Alpha",icon:"",rdns:"a.example"},provider:a},
  ]};
  assert.deepEqual(walletChoices(store,legacy).map(x=>[x.id,x.name,x.provider.label]),[["a","Alpha","a"],["b","Zulu","b"]]);
  assert.deepEqual(walletChoices({getProviders:()=>[]},legacy).map(x=>x.source),["legacy"]);
  assert.deepEqual(walletChoices({getProviders:()=>[]},null),[]);
});

test("connect flow switches or adds pinned Mezo and preserves rejection",async()=>{
  const wallet=await readFile(new URL("../src/wallet.ts",import.meta.url),"utf8");
  const main=await readFile(new URL("../src/main.ts",import.meta.url),"utf8");
  assert.match(wallet,/wallet_switchEthereumChain/);assert.match(wallet,/error\.code!==4902/);
  assert.match(wallet,/wallet_addEthereumChain/);assert.match(wallet,/MEZO_TESTNET\.rpcUrl/);assert.match(wallet,/MEZO_TESTNET\.explorerUrl/);
  assert.match(main,/await switchToMezo\(provider\);[\s\S]*await walletAccount\(provider, true\)/);
});
