import React, { useEffect, useState } from 'react'

export default function DocumentViewer({ fileId, highlight, onClose }: { fileId: string, highlight?: string | null, onClose: ()=>void }){
  const [data, setData] = useState<any>(null)
  const [loading, setLoading] = useState(true)
  useEffect(()=>{
    setLoading(true)
    fetch(`/api/files/${fileId}/content`).then(r=>r.json()).then(d=>{ setData(d); setLoading(false) }).catch(()=>{ setData(null); setLoading(false) })
  },[fileId])

  if (loading) return <div className="popover"><div className="popover-head"><strong>Document</strong><button className="close" onClick={onClose}>×</button></div><div className="popover-body">Loading…</div></div>
  if (!data) return <div className="popover"><div className="popover-head"><strong>Document</strong><button className="close" onClick={onClose}>×</button></div><div className="popover-body">Unable to load document</div></div>

  if (data.type === 'binary') {
    return (
      <div className="popover">
        <div className="popover-head"><strong>{data.filename}</strong><button className="close" onClick={onClose}>×</button></div>
        <div className="popover-body">Binary file — <a href={data.url} target="_blank" rel="noreferrer">download / view</a></div>
      </div>
    )
  }

  // highlight first occurrence
  let content = String(data.content || '')
  let highlighted = content
  if (highlight) {
    const idx = content.indexOf(highlight)
    if (idx >= 0) {
      const before = content.slice(0, idx)
      const match = content.slice(idx, idx + highlight.length)
      const after = content.slice(idx + highlight.length)
      highlighted = before + '<mark>' + escapeHtml(match) + '</mark>' + escapeHtml(after)
    } else {
      highlighted = escapeHtml(content)
    }
  } else {
    highlighted = escapeHtml(content)
  }

  return (
    <div className="popover document-viewer">
      <div className="popover-head"><strong>{data.filename}</strong><button className="close" onClick={onClose}>×</button></div>
      <div className="popover-body"><div className="doc-scroll" dangerouslySetInnerHTML={{ __html: highlighted }} /></div>
    </div>
  )
}

function escapeHtml(s: string) {
  return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/\n/g,'<br/>')
}
