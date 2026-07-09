import React, { useEffect, useState } from 'react'
import Provenance from './Provenance'
import ApprovalPanel from './ApprovalPanel'
import AwardPanel from './AwardPanel'
import BenchmarksPanel from './BenchmarksPanel'

type LineItem = {
  id: string
  label: string
  amountCents: number
  currency: string
  supplierId?: string | null
  confidence?: number
}

type Supplier = { id: string; name: string }

export default function Comparison({ comparisonId }: { comparisonId: string }) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string| null>(null)
  const [suppliers, setSuppliers] = useState<Supplier[]>([])
  const [lineItems, setLineItems] = useState<LineItem[]>([])
  const [openProv, setOpenProv] = useState<string | null>(null)
  const [selectedSupplier, setSelectedSupplier] = useState<string | null>(null)

  useEffect(() => {
    setLoading(true)
    setError(null)
    fetch(`/api/comparisons/${comparisonId}`).then(r => r.json()).then(data => {
      if (data.error) { setError(data.error); setLoading(false); return }
      setSuppliers(data.suppliers || [])
      setLineItems(data.lineItems || [])
      setLoading(false)
    }).catch(err => { setError(String(err)); setLoading(false) })
  }, [comparisonId])

  async function saveEdit(item: LineItem, newAmount: number) {
    const payload = { amountCents: newAmount, userId: 'demo-user', reason: 'manual correction via UI' }
    const res = await fetch(`/api/line-items/${item.id}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) })
    const updated = await res.json()
    if (updated.error) {
      alert('Error: ' + updated.error)
    } else {
      setLineItems(ls => ls.map(l => l.id === item.id ? { ...l, amountCents: updated.amountCents } : l))
    }
  }

  if (loading) return <div className="panel">Loading…</div>
  if (error) return <div className="panel error">{error}</div>

  // group line items by label (rows) and suppliers as columns
  const rows = lineItems
  return (
    <div className="panel">
      <div style={{display:'flex',gap:12}}>
        <div style={{flex:1}}>
          <ApprovalPanel comparisonId={comparisonId} />
          <AwardPanel comparisonId={comparisonId} />
        </div>
        <div style={{width:320}}>
          <div className="panel">
            <h4>Suppliers</h4>
            {suppliers.map(s => <div key={s.id} style={{padding:6, cursor:'pointer'}} onClick={()=>setSelectedSupplier(s.id)}>{s.name}</div>)}
          </div>
          {selectedSupplier && <div style={{marginTop:12}}><OffersPanel supplierId={selectedSupplier} /></div>}
          <div style={{marginTop:12}}>
            <BenchmarksPanel comparisonId={comparisonId} />
          </div>
        </div>
      </div>
      <div className="table">
        <div className="row header">
          <div className="cell label">Item</div>
          {suppliers.map(s => <div key={s.id} className="cell supplier">{s.name}</div>)}
        </div>
        {rows.map(r => (
          <div key={r.id} className="row">
            <div className="cell label">{r.label}</div>
            {suppliers.map(s => {
              const cellItem = lineItems.find(li => li.id === r.id && li.supplierId === s.id) || (r.supplierId === s.id ? r : null)
              const amount = cellItem ? (cellItem.amountCents/100).toFixed(2) : ''
              return (
                <div key={s.id} className="cell supplier numeric">
                  {cellItem ? (
                    <div style={{display:'flex',alignItems:'center',justifyContent:'flex-end',gap:8}}>
                      <EditableAmount item={cellItem} onSave={(n) => saveEdit(cellItem, Math.round(n*100))} />
                      <button className="icon" onClick={()=>setOpenProv(cellItem.id)} title="Provenance">i</button>
                    </div>
                  ) : <span className="muted">—</span>}
                </div>
              )
            })}
          </div>
        ))}
      </div>
      {openProv && <div className="popover-container"><Provenance lineItemId={openProv} onClose={()=>setOpenProv(null)} /></div>}
    </div>
  )
}

function EditableAmount({ item, onSave }: { item: LineItem, onSave: (n:number)=>void }){
  const [editing, setEditing] = useState(false)
  const [val, setVal] = useState((item.amountCents/100).toFixed(2))
  return editing ? (
    <div className="editable">
      <input value={val} onChange={e=>setVal(e.target.value)} />
      <button onClick={()=>{ const n=parseFloat(val)||0; onSave(n); setEditing(false)}}>Save</button>
      <button onClick={()=>{ setVal((item.amountCents/100).toFixed(2)); setEditing(false)}}>Cancel</button>
    </div>
  ) : (
    <div className="value">
      <span className="mono">€{(item.amountCents/100).toFixed(2)}</span>
      <button className="icon" onClick={()=>setEditing(true)}>Edit</button>
    </div>
  )
}
