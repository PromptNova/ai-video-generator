import React, { useEffect, useState } from 'react'

export default function BenchmarksPanel({ comparisonId }: { comparisonId: string }){
  const [bench, setBench] = useState<any|null>(null)
  const [minN, setMinN] = useState(5)

  useEffect(()=>{ if (comparisonId) load() }, [comparisonId, minN])

  async function load(){
    const res = await fetch(`/api/comparisons/${comparisonId}/benchmarks?minN=${minN}`)
    const data = await res.json()
    setBench(data)
  }

  if (!bench) return <div className="panel">Loading benchmarks…</div>

  return (
    <div className="panel">
      <h4>Benchmarks (anonymous)</h4>
      <div style={{marginBottom:8}}>Min datapoints: <input type="number" value={minN} onChange={e=>setMinN(Number(e.target.value))} style={{width:80}} /></div>
      {Object.keys(bench.benchmarks).length===0 ? <div className="muted">No benchmarks</div> : (
        <div>
          {Object.entries(bench.benchmarks).map(([label,info]:any)=> (
            <div key={label} style={{borderTop:'1px solid #f3f4f6',paddingTop:8,marginTop:8}}>
              <div><strong>{label}</strong></div>
              {info.stats ? (
                <div className="muted">mean €{(info.stats.mean/100).toFixed(2)} • median €{(info.stats.median/100).toFixed(2)} • N={info.stats.count}</div>
              ) : (
                <div className="muted">{info.note}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
