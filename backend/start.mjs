import { config } from 'dotenv';
import { resolve } from 'path';
import { fileURLToPath } from 'url';
import { spawn } from 'child_process';

const __dirname = resolve(fileURLToPath(import.meta.url), '..');
config({ path: resolve(__dirname, '.env') });

if (!process.env._DNS_FIXED) {
  const child = spawn(process.execPath, ['--dns-result-order=ipv4first', process.argv[1]], {
    cwd: process.cwd(),
    env: { ...process.env, _DNS_FIXED: '1' },
    stdio: 'inherit',
  });
  child.on('exit', (code) => process.exit(code ?? 0));
} else {
  import('./build/index.js');
}
