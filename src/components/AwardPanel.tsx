import React, { useState } from 'react'

export default function AwardPanel({ comparisonId }: { comparisonId: string }){
  const [supplierId, setSupplierId] = useState('')
  const [reason, setReason] = useState('')

  async function award(){
    const res = await fetch(`/api/comparisons/${comparisonId}/award`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ supplierId, reason, awardedBy: 'decision-maker' }) })
    const data = await res.json()
    if (data.error) alert(data.error)
    else alert('Award recorded')
  }

  async function downloadReport(){
    const res = await fetch(`/api/comparisons/${comparisonId}/award-report`)
    const data = await res.json()
    if (data.url) window.open(data.url, '_blank')
    else alert('Report generation failed')
  }

  return (
    <div className="panel" style={{marginBottom:12}}>
      <h3>Award & Report</h3>
      <div style={{display:'flex',gap:8,alignItems:'center'}}>
        <input placeholder="winner supplier id" value={supplierId} onChange={e=>setSupplierId(e.target.value)} />
        <input placeholder="reason" value={reason} onChange={e=>setReason(e.target.value)} />
        <button onClick={award}>Award</button>
        <button onClick={downloadReport}>Download signed report</button>
      </div>
    </div>
  )
}
