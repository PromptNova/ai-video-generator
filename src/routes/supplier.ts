import express from 'express'
import prisma from '../prisma'
import multer from 'multer'
import path from 'path'
import fs from 'fs'
import { nanoid } from 'nanoid'

const router = express.Router()

const uploadDir = path.join(process.cwd(), 'uploads')
if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir, { recursive: true })

const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, uploadDir),
  filename: (req, file, cb) => cb(null, `${Date.now()}-${file.originalname}`)
})
const upload = multer({ storage })

// Invite: create a submission token for a comparison+optional supplier name
router.post('/comparisons/:id/invite', async (req, res, next) => {
  try {
    const { id: comparisonId } = req.params
    const { supplierName, expiresInHours } = req.body
    const comp = await prisma.comparison.findUnique({ where: { id: comparisonId } })
    if (!comp) return res.status(404).json({ error: 'comparison not found' })
    const token = nanoid(28)
    const expiresAt = expiresInHours ? new Date(Date.now() + expiresInHours * 3600 * 1000) : null
    const st = await prisma.submissionToken.create({ data: { token, comparisonId, supplierName, expiresAt } })
    // public submission URL (assumes FRONTEND_BASE or server host)
    const url = `${req.protocol}://${req.get('host')}/submit/${token}`
    res.json({ token: st.token, url })
  } catch (err) {
    next(err)
  }
})

// Public submission endpoint: accepts multipart/form-data with optional file and/or json field `lineItems`
router.post('/submit/:token', upload.single('file'), async (req, res, next) => {
  try {
    const { token } = req.params
    const t = await prisma.submissionToken.findUnique({ where: { token } })
    if (!t) return res.status(404).json({ error: 'invalid token' })
    if (t.expiresAt && t.expiresAt < new Date()) return res.status(410).json({ error: 'token expired' })

    // supplier info can be in form fields
    const supplierName = req.body.name || t.supplierName || 'Anonymous Supplier'
    const contactEmail = req.body.contactEmail || null

    // create or reuse supplier attached to comparison
    const supplier = await prisma.supplier.create({ data: { name: supplierName, contactEmail, comparisonId: t.comparisonId } })

    // create an Offer (versioning). Attempt to compute next version
    const lastOffer = await prisma.offer.findFirst({ where: { supplierId: supplier.id, comparisonId: t.comparisonId }, orderBy: { createdAt: 'desc' } }).catch(()=>null)
    const nextVersion = lastOffer ? lastOffer.version + 1 : 1
    const offer = await prisma.offer.create({ data: { supplierId: supplier.id, comparisonId: t.comparisonId, fileId: req.file ? undefined : undefined, version: nextVersion } })

    // if a file was uploaded, save record and link to offer
    if (req.file) {
      const uf = await prisma.uploadedFile.create({ data: { path: req.file.path, filename: req.file.originalname, supplierId: supplier.id } })
      await prisma.offer.update({ where: { id: offer.id }, data: { fileId: uf.id } })
    }

    // if JSON lineItems passed
    if (req.body.lineItems) {
      let items = []
      try {
        items = JSON.parse(req.body.lineItems)
      } catch (e) {
        // ignore parse error
      }
      for (const it of items) {
        const amountCents = Math.round((it.amount || 0) * 100)
        await prisma.lineItem.create({ data: {
          comparisonId: t.comparisonId,
          supplierId: supplier.id,
          offerId: offer.id,
          label: it.label || 'item',
          amountCents,
          currency: it.currency || 'EUR',
          sourceFragment: it.sourceFragment || 'submitted-json',
          location: it.location || null,
          confidence: typeof it.confidence === 'number' ? it.confidence : 0.6
        } })
      }
    } else {
      // fallback: create a placeholder stating the supplier uploaded a file
      await prisma.lineItem.create({ data: {
        comparisonId: t.comparisonId,
        supplierId: supplier.id,
        offerId: offer.id,
        label: 'Uploaded offer (needs extraction)',
        amountCents: 0,
        currency: 'EUR',
        sourceFragment: req.file ? `file:${req.file.originalname}` : 'manual-submission',
        confidence: 0.4
      } })
    }

    // Mark token used (do not delete to keep history)
    await prisma.submissionToken.update({ where: { id: t.id }, data: { used: true } })

    res.json({ ok: true, supplierId: supplier.id })
  } catch (err) {
    next(err)
  }
})

export default router
