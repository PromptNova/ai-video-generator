import express from 'express'
import prisma from '../prisma'
import fs from 'fs'
import path from 'path'

const router = express.Router()

function extractTermsFromText(text: string) {
  const results: Array<any> = []

  // payment terms: look for 'net 30', 'net 60', '30 days', 'payment within 30 days'
  const paymentRe = /(?:net\s*)?(\d{1,3})\s*(?:days|day)|net\s*(\d{1,3})/gi
  let m
  while ((m = paymentRe.exec(text))) {
    const days = m[1] || m[2]
    if (days) results.push({ kind: 'payment_term', key: 'payment_days', value: `${days} days`, sourceFragment: m[0], confidence: 0.9 })
  }

  // warranty: 'warranty 12 months', 'guarantee 1 year'
  const warrantyRe = /(warranty|guarantee)\s*(?:of\s*)?(\d{1,2})\s*(months|month|years|year)/gi
  while ((m = warrantyRe.exec(text))) {
    results.push({ kind: 'warranty', key: 'warranty_period', value: `${m[2]} ${m[3]}`, sourceFragment: m[0], confidence: 0.9 })
  }

  // SLA uptime percentage
  const slaRe = /(uptime)\s*(?:of\s*)?(\d{1,3})%/gi
  while ((m = slaRe.exec(text))) {
    results.push({ kind: 'sla', key: 'uptime', value: `${m[2]}%`, sourceFragment: m[0], confidence: 0.9 })
  }

  // liability caps: 'liability limited to €10000' or 'liability cap of 10000'
  const liabilityRe = /(liabilit(?:y|ies)[^\n,.]{0,40}?)(?:to|cap of|limited to)?\s*(€|EUR)?\s?([0-9,.]{3,})/gi
  while ((m = liabilityRe.exec(text))) {
    results.push({ kind: 'liability', key: 'liability_cap', value: `${m[2] || ''}${m[3]}`, sourceFragment: m[0], confidence: 0.85 })
  }

  // termination: 'termination notice 3 months', 'terminate with 30 days'
  const termRe = /(terminate|termination|cancel)\s*(?:with|notice)?\s*(?:of)?\s*(\d{1,3})\s*(days|day|months|month)/gi
  while ((m = termRe.exec(text))) {
    results.push({ kind: 'termination', key: 'termination_notice', value: `${m[2]} ${m[3]}`, sourceFragment: m[0], confidence: 0.88 })
  }

  return results
}

// POST /api/comparisons/:id/extract-terms
// body: { text?: string, fileId?: string, supplierId?: string }
router.post('/comparisons/:id/extract-terms', async (req, res, next) => {
  try {
    const { id: comparisonId } = req.params
    const { text, fileId, supplierId } = req.body
    let content = text || ''

    if (!content && fileId) {
      const file = await prisma.uploadedFile.findUnique({ where: { id: fileId } })
      if (!file) return res.status(404).json({ error: 'file not found' })
      // Only simple text extraction for .txt files; otherwise queue/todo
      if (file.filename.toLowerCase().endsWith('.txt')) {
        content = fs.readFileSync(path.resolve(file.path), 'utf-8')
      } else {
        // create low-confidence placeholder term indicating extraction required
        const placeholder = await prisma.term.create({ data: { comparisonId, supplierId: supplierId || null, kind: 'extraction', key: 'requires_ocr', value: `File ${file.filename} requires OCR/extraction`, sourceFragment: `file:${file.filename}`, confidence: 0.2 } })
        return res.json({ extracted: [placeholder], note: 'Non-text file stored; OCR/extraction TODO' })
      }
    }

    if (!content) return res.status(400).json({ error: 'text or fileId required' })

    const found = extractTermsFromText(content)
    const created: any[] = []
    for (const f of found) {
      const t = await prisma.term.create({ data: { comparisonId, supplierId: supplierId || null, kind: f.kind, key: f.key, value: f.value, sourceFragment: f.sourceFragment, confidence: f.confidence } })
      created.push(t)
    }

    return res.json({ extracted: created })
  } catch (err) {
    next(err)
  }
})

// GET /api/comparisons/:id/terms
router.get('/comparisons/:id/terms', async (req, res, next) => {
  try {
    const terms = await prisma.term.findMany({ where: { comparisonId: req.params.id } })
    res.json(terms)
  } catch (err) {
    next(err)
  }
})

export default router
