import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

const paymentPlan={scheme:"exact",settlement_broadcaster:"facilitator",network:"eip155:31611",chain_id:31611,
  asset:"0x118917a40FAF1CD7a13dB0Ef56C86De7973Ac503",amount_atomic:"10000000000000000",maximum_settlement_submissions:1,
  max_buyer_native_gas_wei:"100000000000000",asset_transfer_method:"permit2",permit2_address:"0x000000000022D473030F116dDEE9F6B43aC78BA3",
  permit2_proxy:"0x402085c248EeA27D92E8b30b2C58ed07f9E20001",approval_mode:"eip2612-gas-sponsoring",required_extension:"eip2612GasSponsoring",
  authorization_identity_version:"liqvera-permit2-eip2612-identity/v1",facilitator_url:"https://facilitator.vativ.io/",rpc_url:"https://rpc.test.mezo.org/",
  database_identity_kind:"sha256-credential-free-postgresql-endpoint/v1",database_host_policy:"loopback-only/v1"};
function canonical(value) {
  if(Array.isArray(value))return `[${value.map(canonical).join(",")}]`;
  if(value&&typeof value==="object")return `{${Object.entries(value).sort(([a],[b])=>a.localeCompare(b)).map(([key,item])=>`${JSON.stringify(key)}:${canonical(item)}`).join(",")}}`;
  return JSON.stringify(value);
}
export const P3_PLAN_DIGEST=createHash("sha256").update(canonical({A13:paymentPlan,A14:paymentPlan})).digest("hex");

if(process.argv[1]&&fileURLToPath(import.meta.url)===process.argv[1]&&process.argv.length===3&&process.argv[2]==="--print-plan-digest")
  process.stdout.write(`${JSON.stringify(P3_PLAN_DIGEST)}\n`);
