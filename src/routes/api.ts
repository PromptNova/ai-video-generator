import express from 'express'
import prisma from '../prisma'

const router = express.Router()

// Teams
router.post('/teams', async (req, res, next) => {
  try {
    const { name } = req.body
    if (!name) return res.status(400).json({ error: 'name required' })
    const team = await prisma.team.create({ data: { name } })
    res.json(team)
  } catch (err) {
    next(err)
  }
})

router.get('/teams/:id', async (req, res, next) => {
  try {
    const team = await prisma.team.findUnique({ where: { id: req.params.id }, include: { users: true, comparisons: true } })
    if (!team) return res.status(404).json({ error: 'team not found' })
    res.json(team)
  } catch (err) {
    next(err)
  }
})

// Users
router.post('/users', async (req, res, next) => {
  try {
    const { email, name, teamId } = req.body
    if (!email) return res.status(400).json({ error: 'email required' })
    const user = await prisma.user.create({ data: { email, name, teamId } })
    res.json(user)
  } catch (err) {
    next(err)
  }
})

// Comparisons
router.post('/comparisons', async (req, res, next) => {
  try {
    const { title, description, teamId } = req.body
    if (!title || !teamId) return res.status(400).json({ error: 'title and teamId required' })
    const comp = await prisma.comparison.create({ data: { title, description, teamId } })
    res.json(comp)
  } catch (err) {
    next(err)
  }
})

router.get('/comparisons/:id', async (req, res, next) => {
  try {
    const comp = await prisma.comparison.findUnique({
      where: { id: req.params.id },
      include: { suppliers: true, lineItems: true, flags: true, statedTotals: true, terms: true }
    })
    if (!comp) return res.status(404).json({ error: 'comparison not found' })
    res.json(comp)
  } catch (err) {
    next(err)
  }
})

// Suppliers
router.post('/suppliers', async (req, res, next) => {
  try {
    const { name, contactEmail, comparisonId } = req.body
    if (!name) return res.status(400).json({ error: 'name required' })
    const supplier = await prisma.supplier.create({ data: { name, contactEmail, comparisonId } })
    res.json(supplier)
  } catch (err) {
    next(err)
  }
})

// Line items
router.post('/line-items', async (req, res, next) => {
  try {
    const { comparisonId, supplierId, label, amountCents, currency, sourceFragment, location, confidence } = req.body
    if (!comparisonId || !supplierId || !label || typeof amountCents !== 'number') return res.status(400).json({ error: 'comparisonId, supplierId, label and amountCents required' })
    const li = await prisma.lineItem.create({ data: { comparisonId, supplierId, label, amountCents, currency, sourceFragment, location, confidence } })
    res.json(li)
  } catch (err) {
    next(err)
  }
})

// Update a line item (manual correction) and record correction for audit/training
router.patch('/line-items/:id', async (req, res, next) => {
  try {
    const { id } = req.params
    const { amountCents, sourceFragment, confidence, userId, reason } = req.body
    const existing = await prisma.lineItem.findUnique({ where: { id } })
    if (!existing) return res.status(404).json({ error: 'line item not found' })

    const updated = await prisma.lineItem.update({ where: { id }, data: {
      amountCents: typeof amountCents === 'number' ? amountCents : existing.amountCents,
      sourceFragment: sourceFragment ?? existing.sourceFragment,
      confidence: typeof confidence === 'number' ? confidence : existing.confidence,
      version: existing.version + 1
    } })

    await prisma.correction.create({ data: {
      lineItemId: existing.id,
      userId: userId ?? null,
      oldAmountCents: existing.amountCents,
      newAmountCents: updated.amountCents,
      reason: reason ?? null
    } })

    res.json(updated)
  } catch (err) {
    next(err)
  }
})

// Flags
router.post('/flags', async (req, res, next) => {
  try {
    const { comparisonId, lineItemId, kind, message } = req.body
    if (!comparisonId || !kind || !message) return res.status(400).json({ error: 'comparisonId, kind and message required' })
    const flag = await prisma.flag.create({ data: { comparisonId, lineItemId, kind, message } })
    res.json(flag)
  } catch (err) {
    next(err)
  }
})

// Stated totals
router.post('/stated-totals', async (req, res, next) => {
  try {
    const { comparisonId, supplierId, amountCents, currency, sourceFragment, location, confidence } = req.body
    if (!comparisonId || !supplierId || typeof amountCents !== 'number') return res.status(400).json({ error: 'comparisonId, supplierId and amountCents required' })
    const st = await prisma.statedTotal.create({ data: { comparisonId, supplierId, amountCents, currency, sourceFragment, location, confidence } })
    res.json(st)
  } catch (err) {
    next(err)
  }
})

// Get provenance for a line item
router.get('/line-items/:id/provenance', async (req, res, next) => {
  try {
    const { id } = req.params
    const li = await prisma.lineItem.findUnique({ where: { id }, include: { comparison: true, supplier: true } })
    if (!li) return res.status(404).json({ error: 'line item not found' })
    // if sourceFragment references a file, try to find uploadedFile
    let file = null
    if (li.sourceFragment && li.sourceFragment.startsWith('file:')) {
      const filename = li.sourceFragment.replace('file:', '')
      file = await prisma.uploadedFile.findFirst({ where: { filename } })
    }
    res.json({ provenance: { sourceFragment: li.sourceFragment, location: li.location, confidence: li.confidence, version: li.version, file } })
  } catch (err) {
    next(err)
  }
})

// Get corrections (audit trail) for a line item
router.get('/line-items/:id/corrections', async (req, res, next) => {
  try {
    const { id } = req.params
    const corrs = await prisma.correction.findMany({ where: { lineItemId: id }, orderBy: { createdAt: 'desc' } })
    res.json(corrs)
  } catch (err) {
    next(err)
  }
})

// Serve file content for uploaded files (text only). For binaries return file info and a download URL.
router.get('/files/:id/content', async (req, res, next) => {
  try {
    const { id } = req.params
    const file = await prisma.uploadedFile.findUnique({ where: { id } })
    if (!file) return res.status(404).json({ error: 'file not found' })
    const fp = file.path
    const lower = file.filename.toLowerCase()
    if (lower.endsWith('.txt') || lower.endsWith('.csv') || lower.endsWith('.md')) {
      const content = await prisma.$queryRawUnsafe(`SELECT readfile(?) as c`, fp).catch(()=>null)
      // Some sqlite setups won't have readfile; fallback to node fs
      if (!content || !content[0]) {
        const fs = require('fs')
        const text = fs.readFileSync(fp, 'utf-8')
        return res.json({ filename: file.filename, type: 'text', content: text })
      }
      return res.json({ filename: file.filename, type: 'text', content: content[0].c })
    }
    // For binaries, provide URL to stored file (server serves /uploads)
    const url = `${req.protocol}://${req.get('host')}/uploads/${encodeURIComponent(file.filename)}`
    res.json({ filename: file.filename, type: 'binary', url })
  } catch (err) {
    next(err)
  }
})

// Submit comparison for approval
router.post('/comparisons/:id/submit-for-approval', async (req, res, next) => {
  try {
    const { id } = req.params
    const { initiatorId, reason } = req.body
    const comp = await prisma.comparison.findUnique({ where: { id } })
    if (!comp) return res.status(404).json({ error: 'comparison not found' })
    const approval = await prisma.approval.create({ data: { comparisonId: id, initiatorId: initiatorId ?? null, reason: reason ?? null } })
    await prisma.approvalAction.create({ data: { approvalId: approval.id, actorId: initiatorId ?? null, action: 'submit', comment: reason ?? null } })
    res.json(approval)
  } catch (err) {
    next(err)
  }
})

// List approvals for a comparison
router.get('/comparisons/:id/approvals', async (req, res, next) => {
  try {
    const { id } = req.params
    const approvals = await prisma.approval.findMany({ where: { comparisonId: id }, include: { actions: true } })
    res.json(approvals)
  } catch (err) {
    next(err)
  }
})

// Get approval details
router.get('/approvals/:id', async (req, res, next) => {
  try {
    const { id } = req.params
    const approval = await prisma.approval.findUnique({ where: { id }, include: { actions: true } })
    if (!approval) return res.status(404).json({ error: 'approval not found' })
    res.json(approval)
  } catch (err) {
    next(err)
  }
})

// Post an action on an approval: approve/reject/comment
router.post('/approvals/:id/action', async (req, res, next) => {
  try {
    const { id } = req.params
    const { actorId, action, comment } = req.body
    const approval = await prisma.approval.findUnique({ where: { id } })
    if (!approval) return res.status(404).json({ error: 'approval not found' })
    if (!['approve','reject','comment'].includes(action)) return res.status(400).json({ error: 'invalid action' })
    const act = await prisma.approvalAction.create({ data: { approvalId: id, actorId: actorId ?? null, action, comment: comment ?? null } })
    if (action === 'approve') {
      await prisma.approval.update({ where: { id }, data: { status: 'approved', approverId: actorId ?? null } })
    } else if (action === 'reject') {
      await prisma.approval.update({ where: { id }, data: { status: 'rejected', approverId: actorId ?? null, reason: comment ?? null } })
    }
    res.json(act)
  } catch (err) {
    next(err)
  }
})

// Award a supplier for a comparison
router.post('/comparisons/:id/award', async (req, res, next) => {
  try {
    const { id } = req.params
    const { supplierId, reason, awardedBy } = req.body
    const comp = await prisma.comparison.findUnique({ where: { id } })
    if (!comp) return res.status(404).json({ error: 'comparison not found' })
    const award = await prisma.award.create({ data: { comparisonId: id, supplierId, reason: reason ?? null, awardedBy: awardedBy ?? null } })
    res.json(award)
  } catch (err) {
    next(err)
  }
})

// List offers for a supplier
router.get('/suppliers/:id/offers', async (req, res, next) => {
  try {
    const { id } = req.params
    const offers = await prisma.offer.findMany({ where: { supplierId: id }, include: { lineItems: true, file: true }, orderBy: { createdAt: 'desc' } })
    res.json(offers)
  } catch (err) {
    next(err)
  }
})

// Diff an offer vs previous offer for same supplier
router.get('/offers/:id/diff-previous', async (req, res, next) => {
  try {
    const { id } = req.params
    const offer = await prisma.offer.findUnique({ where: { id }, include: { lineItems: true, supplier: true, comparison: true } })
    if (!offer) return res.status(404).json({ error: 'offer not found' })
    const previous = await prisma.offer.findFirst({ where: { supplierId: offer.supplierId, comparisonId: offer.comparisonId, id: { not: id } }, orderBy: { createdAt: 'desc' } })
    if (!previous) return res.json({ diff: [], note: 'no previous offer' })
    const prevItems = await prisma.lineItem.findMany({ where: { offerId: previous.id } })
    const currItems = offer.lineItems

    // simple diff by label
    const diffs: any[] = []
    const mapPrev: any = {}
    for (const p of prevItems) mapPrev[p.label] = p
    for (const c of currItems) {
      const p = mapPrev[c.label]
      if (!p) diffs.push({ label: c.label, change: 'added', from: null, to: c.amountCents })
      else if (p.amountCents !== c.amountCents) diffs.push({ label: c.label, change: 'changed', from: p.amountCents, to: c.amountCents })
      delete mapPrev[c.label]
    }
    for (const leftover of Object.values(mapPrev)) diffs.push({ label: leftover.label, change: 'removed', from: leftover.amountCents, to: null })

    res.json({ diff: diffs, previousOfferId: previous.id })
  } catch (err) {
    next(err)
  }
})

// Generate signed audit PDF report for a comparison (saves PDF to reports/ and returns download URL)
router.get('/comparisons/:id/award-report', async (req, res, next) => {
  try {
    const { id } = req.params
    const comp = await prisma.comparison.findUnique({ where: { id }, include: { suppliers: true, lineItems: true, flags: true, statedTotals: true, terms: true } })
    if (!comp) return res.status(404).json({ error: 'comparison not found' })

    // build a simple PDF using pdf-lib
    const { PDFDocument, StandardFonts, rgb } = require('pdf-lib')
    const doc = await PDFDocument.create()
    const page = doc.addPage([595, 842])
    const times = await doc.embedFont(StandardFonts.Helvetica)
    const { width, height } = page.getSize()
    let y = height - 40
    page.drawText(`Forma Comparison Report: ${comp.title}`, { x: 40, y, size: 14, font: times, color: rgb(0,0,0) })
    y -= 24
    page.drawText(`Generated: ${new Date().toISOString()}`, { x: 40, y, size: 10, font: times, color: rgb(0.2,0.2,0.2) })
    y -= 20

    // table header
    page.drawText('Supplier', { x: 40, y, size: 11, font: times })
    page.drawText('Total', { x: 300, y, size: 11, font: times })
    y -= 16

    for (const s of comp.suppliers) {
      const st = comp.statedTotals.find(st => st.supplierId === s.id)
      const total = st ? (st.amountCents / 100).toFixed(2) : (comp.lineItems.filter(li => li.supplierId === s.id).reduce((a,b)=>a+(b.amountCents||0),0)/100).toFixed(2)
      page.drawText(s.name, { x: 40, y, size: 10, font: times })
      page.drawText(`€${total}`, { x: 300, y, size: 10, font: times })
      y -= 14
      if (y < 80) { y = height - 40; page.addPage(); }
    }

    y -= 20
    page.drawText('Flags', { x: 40, y, size: 12, font: times })
    y -= 14
    for (const f of comp.flags) {
      page.drawText(`- ${f.kind}: ${f.message}`, { x: 50, y, size: 10, font: times })
      y -= 12
      if (y < 80) { y = height - 40; page.addPage(); }
    }

    // include simple provenance snippets
    y -= 12
    page.drawText('Terms & provenance', { x: 40, y, size: 12, font: times })
    y -= 14
    for (const t of comp.terms) {
      const v = `${t.kind}/${t.key}: ${t.value}`
      page.drawText(`- ${v}`, { x: 50, y, size: 10, font: times })
      y -= 12
      if (y < 80) { y = height - 40; page.addPage(); }
    }

    // sign: compute a simple audit hash from comparison data
    const crypto = require('crypto')
    const auditString = JSON.stringify({ compId: comp.id, suppliers: comp.suppliers.map(s=>s.id), time: new Date().toISOString() })
    const hash = crypto.createHash('sha256').update(auditString).digest('hex')
    y -= 20
    page.drawText(`Audit signature: ${hash}`, { x: 40, y, size: 8, font: times, color: rgb(0.2,0.2,0.2) })

    const pdfBytes = await doc.save()
    const fs = require('fs')
    const path = require('path')
    const reportsDir = path.join(process.cwd(),'reports')
    if (!fs.existsSync(reportsDir)) fs.mkdirSync(reportsDir,{recursive:true})
    const filename = `report-${comp.id}-${Date.now()}.pdf`
    const filepath = path.join(reportsDir, filename)
    fs.writeFileSync(filepath, pdfBytes)

    // persist SignedReport
    const sr = await prisma.signedReport.create({ data: { comparisonId: comp.id, path: `/reports/${filename}`, hash } })

    res.json({ url: `${req.protocol}://${req.get('host')}/reports/${encodeURIComponent(filename)}`, hash })
  } catch (err) {
    next(err)
  }
})

export default router
