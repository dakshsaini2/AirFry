import axios from 'axios';

const api = axios.create({
  baseURL: '/api'
});

export const getRoutes = () => api.get('/routes').then(res => res.data);
export const getSummary = (params: any) => api.get('/summary', { params }).then(res => res.data);
export const getIndex = (params: any) => api.get('/index', { params }).then(res => res.data);
export const getElasticity = (params: any) => api.get('/elasticity', { params }).then(res => res.data);
export const getHeatmap = () => api.get('/heatmap').then(res => res.data);
export const getCarriers = () => api.get('/carriers').then(res => res.data);
export const getBacktest = () => api.get('/backtest').then(res => res.data);
export const getQuality = () => api.get('/quality').then(res => res.data);
export const getFares = (params: any) => api.get('/fares', { params }).then(res => res.data);
export const getMospi = () => api.get('/mospi').then(res => res.data);
export const getValidationReport = () => api.get('/v1/validation_report').then(res => res.data);
export const runScrape = () => api.post('/scrape').then(res => res.data);
