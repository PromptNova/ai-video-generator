import React, { useEffect, useState } from 'react'
import DocumentViewer from './DocumentViewer'

export default function Provenance({ lineItemId, onClose }: { lineItemId: string, onClose: ()=>void }){
  const [prov, setProv] = useState<any>(null)
  const [corrs, setCorrs] = useState<any[]>([])
  const [openFileId, setOpenFileId] = useState<string|null>(null)
  useEffect(()=>{
    fetch(`/api/line-items/${lineItemId}/provenance`).then(r=>r.json()).then(d=>setProv(d.provenance)).catch(()=>setProv(null))
    fetch(`/api/line-items/${lineItemId}/corrections`).then(r=>r.json()).then(d=>setCorrs(d)).catch(()=>setCorrs([]))
  },[lineItemId])

  return (
    <div className="popover">
      <div className="popover-head">
        <strong>Provenance</strong>
        <button className="close" onClick={onClose}>×</button>
      </div>
      {!prov ? <div className="popover-body">No provenance available.</div> : (
        <div className="popover-body">
          <div><strong>Source:</strong> {prov.sourceFragment || '—'}</div>
          <div><strong>Location:</strong> {prov.location || '—'}</div>
          <div><strong>Confidence:</strong> {(prov.confidence||0).toFixed(2)}</div>
          <div><strong>Version:</strong> {prov.version}</div>
          {prov.file && <div><strong>Uploaded file:</strong> <a href={`/${prov.file.path}`} target="_blank" rel="noreferrer">{prov.file.filename}</a> <button onClick={()=>setOpenFileId(prov.file.id)} className="icon">View</button></div>}
        </div>
      )}

      <div className="popover-head" style={{marginTop:8}}><strong>Correction history</strong></div>
      <div className="popover-body">
          {corrs.length===0 ? <div className="muted">No corrections</div> : corrs.map(c=> (
          <div key={c.id} className="corr">
            <div className="mono">Old: €{(c.oldAmountCents/100).toFixed(2)} → New: €{(c.newAmountCents/100).toFixed(2)}</div>
            <div className="muted">By: {c.userId||'unknown'} • {new Date(c.createdAt).toLocaleString()}</div>
            {c.reason && <div className="muted">Reason: {c.reason}</div>}
          </div>
        ))}
      </div>
      {openFileId && <div className="popover-container"><DocumentViewer fileId={openFileId} highlight={prov?.sourceFragment} onClose={()=>setOpenFileId(null)} /></div>}
    </div>
  )
}
