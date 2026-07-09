import React, { useEffect, useState } from 'react'

export default function ApprovalPanel({ comparisonId }: { comparisonId: string }){
  const [approvals, setApprovals] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [comment, setComment] = useState('')

  useEffect(()=>{ fetchApprovals() }, [comparisonId])

  async function fetchApprovals(){
    setLoading(true)
    const res = await fetch(`/api/comparisons/${comparisonId}/approvals`)
    const data = await res.json()
    setApprovals(data || [])
    setLoading(false)
  }

  async function submitForApproval(){
    const res = await fetch(`/api/comparisons/${comparisonId}/submit-for-approval`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ initiatorId: 'demo-user', reason: comment }) })
    const data = await res.json()
    await fetchApprovals()
  }

  async function act(approvalId: string, action: 'approve'|'reject'){
    const comment = prompt(`Add comment for ${action}`) || ''
    await fetch(`/api/approvals/${approvalId}/action`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ actorId: 'approver-user', action, comment }) })
    await fetchApprovals()
  }

  return (
    <div className="panel">
      <h3>Approval</h3>
      <div style={{marginBottom:8}}>
        <textarea placeholder="Optional reason/comment" value={comment} onChange={e=>setComment(e.target.value)} style={{width:'100%',height:60}} />
        <button onClick={submitForApproval} style={{marginTop:8}}>Submit for approval</button>
      </div>
      <div>
        <strong>Approvals</strong>
        {loading ? <div>Loading…</div> : approvals.length===0 ? <div className="muted">No approvals yet</div> : approvals.map(a=> (
          <div key={a.id} style={{borderTop:'1px solid #f3f4f6',paddingTop:8,marginTop:8}}>
            <div><strong>Status:</strong> {a.status}</div>
            <div className="muted">Initiator: {a.initiatorId || 'unknown'} • {new Date(a.createdAt).toLocaleString()}</div>
            <div className="muted">Reason: {a.reason || '—'}</div>
            <div style={{marginTop:6}}>
              <button onClick={()=>act(a.id,'approve')}>Approve</button>
              <button onClick={()=>act(a.id,'reject')} style={{marginLeft:8}}>Reject</button>
            </div>
            {a.actions && a.actions.length>0 && (
              <div className="muted" style={{marginTop:6}}>Actions:
                {a.actions.map((ac:any)=> <div key={ac.id} className="muted">{ac.action} by {ac.actorId||'unknown'} • {new Date(ac.createdAt).toLocaleString()} {ac.comment?` - ${ac.comment}`:''}</div>)}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
