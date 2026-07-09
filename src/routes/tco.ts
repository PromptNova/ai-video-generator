import express from 'express'
import prisma from '../prisma'

const router = express.Router()

// Default weights
const DEFAULT_WEIGHTS = {
  deliveryDaysCostCentsPerDay: 200, // €2 per day
  incotermPenaltiesPercent: { EXW: 8, FCA: 4 },
  missingItemPenaltyCents: 5000, // €50 per missing item
  lowConfidencePercent: 2 // percent of amount added when confidence low
}

function parseWeights(bodyWeights: any) {
  const w = { ...DEFAULT_WEIGHTS }
  if (!bodyWeights) return w
  if (typeof bodyWeights.deliveryDaysCostCentsPerDay === 'number') w.deliveryDaysCostCentsPerDay = bodyWeights.deliveryDaysCostCentsPerDay
  if (bodyWeights.incotermPenaltiesPercent) w.incotermPenaltiesPercent = { ...w.incotermPenaltiesPercent, ...bodyWeights.incotermPenaltiesPercent }
  if (typeof bodyWeights.missingItemPenaltyCents === 'number') w.missingItemPenaltyCents = bodyWeights.missingItemPenaltyCents
  if (typeof bodyWeights.lowConfidencePercent === 'number') w.lowConfidencePercent = bodyWeights.lowConfidencePercent
  return w
}

// Compute TCO for a comparison
// POST /api/comparisons/:id/compute-tco
// body: { weights?: {...}, saveConfig?: boolean }
router.post('/comparisons/:id/compute-tco', async (req, res, next) => {
  try {
    const comparisonId = req.params.id
    const { weights: bodyWeights, saveConfig } = req.body
    const weights = parseWeights(bodyWeights)

    const comp = await prisma.comparison.findUnique({ where: { id: comparisonId }, include: { suppliers: true, lineItems: true, statedTotals: true } })
    if (!comp) return res.status(404).json({ error: 'comparison not found' })

    // Build RFQ template labels to detect missing items (lineItems with supplierId null created from RFQ have sourceFragment starting with 'rfq:')
    const templateItems = comp.lineItems.filter(li => !li.supplierId && li.sourceFragment && li.sourceFragment.startsWith('rfq:')).map(li => li.label)

    const results: any[] = []
    for (const supplier of comp.suppliers) {
      // base amount: prefer statedTotal for this supplier, else sum of supplier lineItems
      const stated = comp.statedTotals.find(st => st.supplierId === supplier.id)
      let baseCents = stated ? stated.amountCents : 0
      if (!baseCents) {
        const items = comp.lineItems.filter(li => li.supplierId === supplier.id)
        baseCents = items.reduce((s, it) => s + (it.amountCents || 0), 0)
      }

      const breakdown: any = { baseCents }

      // delivery penalty heuristic: look for a lineItem labelled like 'delivery X days' or a term
      const deliveryTerm = await prisma.term.findFirst({ where: { comparisonId, supplierId: supplier.id, kind: 'delivery_time' } })
      let deliveryDays = 0
      if (deliveryTerm) {
        const m = String(deliveryTerm.value).match(/(\d{1,3})/) 
        if (m) deliveryDays = parseInt(m[1], 10)
      }
      const deliveryPenalty = Math.round(deliveryDays * weights.deliveryDaysCostCentsPerDay)
      breakdown.deliveryPenalty = deliveryPenalty

      // incoterm penalty
      const incoterm = supplier.incoterm || 'UNKNOWN'
      const incotermPenaltyPercent = weights.incotermPenaltiesPercent[incoterm] || 0
      const incotermPenalty = Math.round(baseCents * (incotermPenaltyPercent / 100))
      breakdown.incoterm = { incoterm, incotermPenaltyPercent, incotermPenalty }

      // missing items
      let missingCount = 0
      if (templateItems.length) {
        const supplierLabels = comp.lineItems.filter(li => li.supplierId === supplier.id).map(li => li.label)
        for (const t of templateItems) if (!supplierLabels.includes(t)) missingCount++
      }
      const missingPenalty = missingCount * weights.missingItemPenaltyCents
      breakdown.missingCount = missingCount
      breakdown.missingPenalty = missingPenalty

      // low confidence penalty
      const supplierItems = comp.lineItems.filter(li => li.supplierId === supplier.id)
      let lowConfidencePenalty = 0
      for (const it of supplierItems) {
        if ((it.confidence ?? 1) < 0.7) {
          lowConfidencePenalty += Math.round((it.amountCents || 0) * (weights.lowConfidencePercent / 100))
        }
      }
      breakdown.lowConfidencePenalty = lowConfidencePenalty

      const total = baseCents + deliveryPenalty + incotermPenalty + missingPenalty + lowConfidencePenalty

      // human-readable reason
      const reason = []
      if (incotermPenalty > 0) reason.push(`Incoterm ${incoterm} adds €${(incotermPenalty/100).toFixed(2)}`)
      if (missingPenalty > 0) reason.push(`Missing ${missingCount} RFQ items, penalty €${(missingPenalty/100).toFixed(2)}`)
      if (lowConfidencePenalty > 0) reason.push(`Low-confidence items add €${(lowConfidencePenalty/100).toFixed(2)}`)
      if (deliveryPenalty > 0) reason.push(`Delivery time adds €${(deliveryPenalty/100).toFixed(2)}`)

      const result = { supplierId: supplier.id, supplierName: supplier.name, breakdown, totalCents: total, reason: reason.join('; ') }

      // persist TCOResult
      await prisma.tCOResult.create({ data: { comparisonId, supplierId: supplier.id, totalCents: total, breakdown: JSON.stringify(breakdown) } })

      results.push(result)
    }

    // optionally save config
    if (saveConfig) {
      const cfgJson = JSON.stringify(weights)
      const existing = await prisma.tCOConfig.findUnique({ where: { comparisonId } }).catch(() => null)
      if (existing) {
        await prisma.tCOConfig.update({ where: { comparisonId }, data: { weightsJson: cfgJson } })
      } else {
        await prisma.tCOConfig.create({ data: { comparisonId, weightsJson: cfgJson } })
      }
    }

    res.json({ results })
  } catch (err) {
    next(err)
  }
})

export default router
