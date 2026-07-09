import React, { useEffect, useState } from 'react'

export default function OffersPanel({ supplierId }: { supplierId: string }){
  const [offers, setOffers] = useState<any[]>([])
  const [selected, setSelected] = useState<string | null>(null)
  const [diff, setDiff] = useState<any[] | null>(null)

  useEffect(()=>{ if (supplierId) load() }, [supplierId])

  async function load(){
    const res = await fetch(`/api/suppliers/${supplierId}/offers`)
    const data = await res.json()
    setOffers(data || [])
  }

  async function showDiff(offerId: string){
    const res = await fetch(`/api/offers/${offerId}/diff-previous`)
    const data = await res.json()
    setSelected(offerId)
    setDiff(data.diff || [])
  }

  if (!supplierId) return <div className="muted">Select a supplier to view offers</div>

  return (
    <div className="panel">
      <h4>Offers</h4>
      {offers.length===0 ? <div className="muted">No offers yet</div> : (
        <div>
          {offers.map(o => (
            <div key={o.id} style={{borderTop:'1px solid #f3f4f6',paddingTop:8,marginTop:8}}>
              <div><strong>Offer v{o.version}</strong> • {new Date(o.createdAt).toLocaleString()}</div>
              <div className="muted">File: {o.file?.filename || '—'}</div>
              <div style={{marginTop:6}}>
                <button onClick={()=>showDiff(o.id)}>Show diff vs previous</button>
              </div>
            </div>
          ))}
        </div>
      )}

      {diff && (
        <div style={{marginTop:12}}>
          <strong>Diff</strong>
          {diff.length===0 ? <div className="muted">No changes</div> : diff.map(d => (
            <div key={d.label} style={{paddingTop:6}}>
              <div>{d.label}: {d.change} {d.from!=null?`€${(d.from/100).toFixed(2)}`:'—'} → {d.to!=null?`€${(d.to/100).toFixed(2)}`:'—'}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
