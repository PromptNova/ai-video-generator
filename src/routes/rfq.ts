import express from 'express'
import prisma from '../prisma'

const router = express.Router()

// Create an RFQ with items
router.post('/rfqs', async (req, res, next) => {
  try {
    const { title, description, teamId, items } = req.body
    if (!title || !items || !Array.isArray(items)) return res.status(400).json({ error: 'title and items[] required' })
    const rfq = await prisma.rFQ.create({ data: { title, description, teamId, items: { create: items.map((it: any) => ({ label: it.label, quantity: it.quantity || 1, unit: it.unit || null, expectedAmountCents: it.expectedAmountCents || null })) } }, include: { items: true } })
    res.json(rfq)
  } catch (err) {
    next(err)
  }
})

router.get('/rfqs/:id', async (req, res, next) => {
  try {
    const rfq = await prisma.rFQ.findUnique({ where: { id: req.params.id }, include: { items: true } })
    if (!rfq) return res.status(404).json({ error: 'rfq not found' })
    res.json(rfq)
  } catch (err) {
    next(err)
  }
})

// Send RFQ: create an empty comparison pre-populated with RFQ rows
router.post('/rfqs/:id/send', async (req, res, next) => {
  try {
    const { id } = req.params
    const rfq = await prisma.rFQ.findUnique({ where: { id }, include: { items: true, team: true } })
    if (!rfq) return res.status(404).json({ error: 'rfq not found' })

    // create comparison
    const comp = await prisma.comparison.create({ data: { title: `RFQ: ${rfq.title}`, description: rfq.description || undefined, teamId: rfq.teamId || undefined } })

    // create template line items for each RFQ item (supplierId left null so they are rows to be filled)
    for (const it of rfq.items) {
      await prisma.lineItem.create({ data: { comparisonId: comp.id, supplierId: null, label: it.label, amountCents: it.expectedAmountCents ?? 0, currency: 'EUR', sourceFragment: `rfq:${rfq.id}:item:${it.id}`, confidence: 1.0 } })
    }

    res.json({ comparisonId: comp.id })
  } catch (err) {
    next(err)
  }
})

export default router
