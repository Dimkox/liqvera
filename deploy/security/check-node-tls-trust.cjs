// Offline regression for Node's default TLS store and startup inheritance.
const assert = require('node:assert/strict');
const { X509Certificate } = require('node:crypto');
const { execFileSync } = require('node:child_process');
const tls = require('node:tls');
const { delimiter } = require('node:path');

const compromised = new Set([
  '86A1ECBA089C4A8D3BBE2734C612BA341D813E043CF9E8A862CD5C57A36BBE6B',
  'D7A7A0FB5D7E2731D771E9484EBCDEF71D5F0C3E0A2948782BC83EE0EA699EF4',
  '7DD78D5F4F13459A83DFF9ABBBA62EDBAF6F2D102BF257FD712F4D9F2746ED8D',
  'F2EDAAFF3D9B701FB4D14C9F285F8C0BAD90FC3BCC1FA07D47F4718EDABA34A5',
]);
// OpenSSL roots are intentionally absent from Node's 'default' enumeration.
// Require the explicit, inherited mode and inspect its system store plus extras.
assert.equal(process.env.NODE_OPTIONS, '--use-openssl-ca', 'OpenSSL trust mode must reach spawned Node processes');
// Node's enumeration does not split OpenSSL's directory list. Reject this
// unsupported override rather than overlooking lazily loaded certificates.
assert(!process.env.SSL_CERT_DIR?.includes(delimiter), 'Multiple CA directories require separate inspection');
const roots = [...tls.getCACertificates('system'), ...tls.getCACertificates('extra')];
const fingerprints = new Set(roots.map(root => new X509Certificate(root).fingerprint256.replaceAll(':', '')));
assert(fingerprints.size > 50, 'Effective trust store is unexpectedly empty or truncated');
for (const fingerprint of fingerprints) {
  assert(!compromised.has(fingerprint), 'Compromised emSign root remains in effective Node trust');
}
assert.notEqual(process.env.NODE_TLS_REJECT_UNAUTHORIZED, '0', 'TLS verification must remain enabled');
console.log(JSON.stringify({ node: process.version, openssl: process.versions.openssl,
  effective_roots: fingerprints.size, compromised_roots: 0, tls_verification: 'required',
  process: process.argv.includes('--child') ? 'child' : 'parent' }));
if (!process.argv.includes('--child')) {
  // Match gateway-entrypoint's spawn semantics: NODE_OPTIONS must be inherited.
  process.stdout.write(execFileSync(process.execPath, [__filename, '--child'], { env: process.env }));
}
