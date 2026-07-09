import express from 'express'
import cors from 'cors'
import apiRouter from './routes/api'
import supplierRouter from './routes/supplier'
import rfqRouter from './routes/rfq'
import termsRouter from './routes/terms'
import tcoRouter from './routes/tco'
import reportsRouter from './routes/reportsStatic'
import benchmarkRouter from './routes/benchmark'
import prisma from './prisma'

const app = express()
app.use(cors())
app.use(express.json({ limit: '5mb' }))

app.use('/api', apiRouter)
app.use('/api', supplierRouter)
app.use('/api', rfqRouter)
app.use('/api', termsRouter)
app.use('/api', tcoRouter)

// serve generated reports
app.use('/', reportsRouter)
app.use('/api', benchmarkRouter)

// expose uploads for diagnostics (in prod put behind auth or object store)
app.use('/uploads', express.static('uploads'))

app.get('/health', async (req, res) => {
  try {
    await prisma.$queryRaw`SELECT 1`
    res.json({ status: 'ok' })
  } catch (err) {
    res.status(500).json({ status: 'db error', error: String(err) })
  }
})

// central error handler
app.use((err: any, req: any, res: any, next: any) => {
  console.error(err)
  res.status(500).json({ error: err?.message ?? 'internal error' })
})

const PORT = process.env.PORT || 4000
app.listen(PORT, () => console.log(`Server listening on ${PORT}`))
