import net from 'node:net';

const sockets = new Set();
const server = net.createServer({ pauseOnConnect: true }, (client) => {
  if (!['127.0.0.1', '::ffff:127.0.0.1'].includes(client.remoteAddress ?? '')) {
    client.destroy();
    return;
  }
  if (sockets.size >= 64) {
    client.destroy();
    return;
  }
  const upstream = net.createConnection({ host: 'postgres', port: 5432 });
  sockets.add(client);
  const close = () => { sockets.delete(client); client.destroy(); upstream.destroy(); };
  client.setTimeout(30_000, close);
  upstream.setTimeout(30_000, close);
  client.on('error', close).on('close', close);
  upstream.on('error', close).on('close', close).on('connect', () => {
    client.pipe(upstream);
    upstream.pipe(client);
    client.resume();
  });
});

server.maxConnections = 64;
server.listen(5432, '127.0.0.1');
