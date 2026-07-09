import express from 'express'
import path from 'path'

const router = express.Router()

// Serve reports directory
router.use('/reports', express.static(path.join(process.cwd(),'reports')))

export default router
