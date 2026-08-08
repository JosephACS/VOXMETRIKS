import path from 'path';

export const AUTH_DIR = path.join(__dirname, '..', '.auth');
export const DEMO_AUTH_FILE = path.join(AUTH_DIR, 'demo.json');
export const ADMIN_AUTH_FILE = path.join(AUTH_DIR, 'admin.json');

export const BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? 'http://127.0.0.1:4200';
export const API_URL = process.env.PLAYWRIGHT_API_URL ?? 'http://127.0.0.1:8000';
