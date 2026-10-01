import assert from "node:assert/strict";
import test from "node:test";
import { discoverWalletChoices, walletChoices } from "../src/wallet-discovery.ts";
import { switchToMezo } from "../src/wallet.ts";
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

test("connect-time discovery explicitly requests late EIP-6963 providers",async()=>{
  const announced=[];const late=provider("late");
  const store={getProviders:()=>announced};
  const target={dispatchEvent(event){
    assert.equal(event.type,"eip6963:requestProvider");
    announced.push({info:{uuid:"late",name:"Late wallet",icon:"",rdns:"late.example"},provider:late});
    return true;
  }};
  const found=await discoverWalletChoices(store,null,target,0);
  assert.deepEqual(found.map(x=>[x.id,x.provider.label]),[["late","late"]]);
});

test("switch flow uses exact pinned Mezo parameters and fails closed",async()=>{
  let chain="0x1";const calls=[];
  const existing={async request(input){calls.push(input);if(input.method==="wallet_switchEthereumChain")chain="0x7b7b";if(input.method==="eth_chainId")return chain;return null;}};
  await switchToMezo(existing);
  assert.deepEqual(calls,[{method:"wallet_switchEthereumChain",params:[{chainId:"0x7b7b"}]},{method:"eth_chainId"}]);

  chain="0x1";calls.length=0;
  const unknown={async request(input){calls.push(input);if(input.method==="wallet_switchEthereumChain")throw {code:4902};if(input.method==="wallet_addEthereumChain")chain="0x7b7b";if(input.method==="eth_chainId")return chain;return null;}};
  await switchToMezo(unknown);
  assert.deepEqual(calls[1],{method:"wallet_addEthereumChain",params:[{chainId:"0x7b7b",chainName:"Mezo Matsnet",
    nativeCurrency:{name:"Bitcoin",symbol:"BTC",decimals:18},rpcUrls:["https://rpc.test.mezo.org"],blockExplorerUrls:["https://explorer.test.mezo.org"]}]});
  assert.equal(calls.at(-1).method,"eth_chainId");

  await assert.rejects(()=>switchToMezo({async request(input){if(input.method==="wallet_switchEthereumChain")throw {code:4001};}}),error=>error.code===4001);
  await assert.rejects(()=>switchToMezo({async request(input){if(input.method==="wallet_switchEthereumChain")return null;if(input.method==="eth_chainId")return "0x1";}}),/different network/);

  const main=await readFile(new URL("../src/main.ts",import.meta.url),"utf8");
  assert.match(main,/await switchToMezo\(provider\);[\s\S]*await walletAccount\(provider, true\)/);
  assert.match(main,/await discoverWalletChoices\(walletStore,injectedWallet\(\)\)/);
});
