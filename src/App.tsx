import React, { useState } from 'react'
import Comparison from './components/Comparison'

export default function App() {
  const [comparisonId, setComparisonId] = useState('')
  return (
    <div className="app-root">
      <header className="app-header">
        <h1>Forma — Comparison</h1>
        <div className="input-row">
          <input placeholder="Enter comparison id" value={comparisonId} onChange={e => setComparisonId(e.target.value)} />
        </div>
      </header>
      <main>
        {comparisonId ? <Comparison comparisonId={comparisonId} /> : <div className="empty">Enter a comparison id to view</div>}
      </main>
    </div>
  )
}
