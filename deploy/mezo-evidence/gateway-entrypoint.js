// Build the database URL from the Compose secret without printing it or placing it in a shell command.
const { readFileSync } = require('node:fs');
const { spawn } = require('node:child_process');

const secretPath = process.env.LIQVERA_POSTGRES_PASSWORD_FILE || '/run/secrets/postgres_password';
const password = readFileSync(secretPath, 'utf8').trimEnd();
if (!password) throw new Error('PostgreSQL password file is empty');
const url = new URL('postgresql://liqvera@postgres:5432/liqvera');
url.password = password;

const command = process.argv[2] || 'npm';
const args = process.argv.length > 2 ? process.argv.slice(3) : ['start'];
const isMigration = command === 'npm' && args[0] === 'run' && args[1] === 'migrate';
if (!isMigration) {
  const reportTokenPath = process.env.REPORT_SERVICE_TOKEN_FILE;
  if (!reportTokenPath || !readFileSync(reportTokenPath, 'utf8').trim()) {
    throw new Error('Internal report token file is missing or empty');
  }
}
const child = spawn(command, args, {
  cwd: '/workspace/apps/mezo-gateway',
  env: { ...process.env, DATABASE_URL: url.toString() },
  stdio: 'inherit',
});
child.on('error', (error) => {
  process.stderr.write(`Gateway process failed to start: ${error.message}\n`);
  process.exit(1);
});
for (const signal of ['SIGTERM', 'SIGINT']) {
  process.on(signal, () => child.kill(signal));
}
child.on('exit', (code, signal) => {
  process.exit(signal ? 1 : (code ?? 1));
});
