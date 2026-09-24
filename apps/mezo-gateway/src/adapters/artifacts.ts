import { constants } from 'node:fs';
import { lstat, open, realpath } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { type Artifact, PublicError, uuidPattern } from '../domain/model.js';
import type { ArtifactStore } from '../ports/index.js';
import { digest } from '../security/input.js';
export class ImmutableArtifacts implements ArtifactStore {
  constructor(private readonly root: string) {}
  async healthy(): Promise<boolean> {
    try { const info=await lstat(this.root); return info.isDirectory() && !info.isSymbolicLink(); } catch { return false; }
  }
  private async directory(id: string): Promise<string> {
    if (!uuidPattern.test(id)) throw new PublicError('ARTIFACT_INTEGRITY_FAILURE');
    const root=await realpath(this.root); const path=join(root,id);
    const stat=await lstat(path);
    if (!stat.isDirectory() || stat.isSymbolicLink() || await realpath(path)!==resolve(root,id)) throw new PublicError('ARTIFACT_INTEGRITY_FAILURE');
    return path;
  }
  async read(artifact: Artifact, kind: 'report'|'bundle'): Promise<Buffer> {
    try {
      const path=join(await this.directory(artifact.report_id),kind==='report'?'report.json':'evidence.zip');
      const file=await open(path,constants.O_RDONLY|constants.O_NOFOLLOW);
      try {
        const stat=await file.stat(); const limit=kind==='report'?1048576:10485760;
        const expectedSize=kind==='report'?artifact.report_size_bytes:artifact.bundle_size_bytes;
        if (!stat.isFile() || stat.size<1 || stat.size>limit || stat.size!==expectedSize) throw new PublicError('ARTIFACT_INTEGRITY_FAILURE');
        // Bounded buffer even if the underlying file is concurrently enlarged.
        const bytes=Buffer.alloc(stat.size+1); let offset=0;
        while(offset<bytes.length) { const read=await file.read(bytes,offset,bytes.length-offset,offset); if(!read.bytesRead)break; offset+=read.bytesRead; }
        const result=bytes.subarray(0,offset);
        if (offset!==expectedSize || digest(result)!==(kind==='report'?artifact.report_sha256:artifact.bundle_sha256)) throw new PublicError('ARTIFACT_INTEGRITY_FAILURE');
        return result;
      } finally { await file.close(); }
    } catch { throw new PublicError('ARTIFACT_INTEGRITY_FAILURE'); }
  }
}
