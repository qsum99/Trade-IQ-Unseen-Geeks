@echo off
title TradeIQ Next.js Dev Server
cd /d "%~dp0frontend"
echo ====================================================
echo Starting TradeIQ Next.js Frontend Dev Server...
echo Open http://localhost:3000 in your browser when ready.
echo ====================================================
echo.
npm run dev
pause
