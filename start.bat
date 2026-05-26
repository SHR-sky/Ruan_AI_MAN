@echo off
chcp 65001 >nul
title 景区导览AI数字人 - 一键启动

echo ========================================
echo  景区导览AI数字人 - 一键启动脚本
echo ========================================
echo.

:: 激活 conda 环境
call conda activate aiman
if %errorlevel% neq 0 (
    echo [错误] 无法激活 conda 环境 "aiman"，请确认 Conda 已正确安装
    pause
    exit /b 1
)

:: 启动后端 (新窗口)
echo [1/3] 启动后端服务 (uvicorn)...
start "后端服务" cmd /c "conda activate aiman && cd /d "%~dp0backend" && uvicorn app.main:app --reload --host 0.0.0.0 --port 8001"

:: 等待后端准备
timeout /t 3 /nobreak >nul

:: 启动前端 (新窗口)
echo [2/3] 启动游客前端 (Vite)...
start "游客前端" cmd /c "cd /d "%~dp0frontend" && npm run dev"

:: 启动管理后台 (新窗口)
echo [3/3] 启动管理后台 (Vite)...
start "管理后台" cmd /c "cd /d "%~dp0admin" && npm run dev"

echo.
echo 所有服务已启动！
echo.
echo  游客前端: http://localhost:5173
echo  管理后台: http://localhost:5174
echo  后端 API: http://localhost:8001
echo.
echo 关闭窗口即可停止对应服务。
echo.

pause
