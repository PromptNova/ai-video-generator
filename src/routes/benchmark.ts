import express from 'express'
import prisma from '../prisma'

const router = express.Router()

function statsFromCents(arr: number[]) {
  if (!arr.length) return null
  arr.sort((a,b)=>a-b)
  const sum = arr.reduce((s,n)=>s+n,0)
  const mean = sum / arr.length
  const median = arr.length%2===1 ? arr[(arr.length-1)/2] : (arr[arr.length/2-1]+arr[arr.length/2])/2
  const sq = arr.reduce((s,n)=>s+Math.pow(n-mean,2),0)
  const std = Math.sqrt(sq / arr.length)
  const p25 = arr[Math.floor(arr.length*0.25)]
  const p75 = arr[Math.floor(arr.length*0.75)]
  return { count: arr.length, mean: Math.round(mean), median: Math.round(median), std: Math.round(std), p25: Math.round(p25), p75: Math.round(p75) }
}

// GET /api/comparisons/:id/benchmarks?minN=5
// Returns anonymized aggregated benchmarks per label present in the comparison.
router.get('/comparisons/:id/benchmarks', async (req, res, next) => {
  try {
    const comparisonId = req.params.id
    const minN = Number(req.query.minN || 5)
    const comp = await prisma.comparison.findUnique({ where: { id: comparisonId }, include: { lineItems: true } })
    if (!comp) return res.status(404).json({ error: 'comparison not found' })

    // derive labels to benchmark (unique normalized labels from comparison)
    const labels = Array.from(new Set(comp.lineItems.map(li => (li.label || '').trim()))).filter(l=>l)
    const out: any = {}
    for (const label of labels) {
      // gather matching line items across DB with same label (case-insensitive fallback: contains)
      const matches = await prisma.lineItem.findMany({ where: { label: { contains: label } }, select: { amountCents: true } })
      const amounts = matches.map(m=>m.amountCents)
      if (amounts.length >= minN) {
        const s = statsFromCents(amounts)
        out[label] = { stats: s }
      } else {
        out[label] = { stats: null, note: `insufficient data (need ${minN})` }
      }
    }

    res.json({ benchmarks: out, minN })
  } catch (err) {
    next(err)
  }
})

export default router
