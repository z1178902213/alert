@echo off
chcp 65001 >nul
title 打包思源笔记提醒器
echo 正在打包思源笔记提醒器为exe文件...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到Python，请先安装Python 3.6+
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查PyInstaller是否安装
echo 检查PyInstaller...
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo 正在安装PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo 安装PyInstaller失败，请检查网络连接
        pause
        exit /b 1
    )
)

echo.
echo 开始打包程序...
echo 这可能需要几分钟时间，请耐心等待...
echo.

REM 使用PyInstaller打包
pyinstaller --onefile --windowed --name "思源笔记提醒器" --distpath "./dist" --workpath "./build" --specpath "./build" alert.py

if errorlevel 1 (
    echo.
    echo 打包失败！请检查错误信息
    pause
    exit /b 1
)

echo.
echo 打包完成！
echo.
echo 生成的文件位置：
echo - exe文件：./dist/思源笔记提醒器.exe
echo - 构建文件：./build/（可以删除）
echo.
echo 现在您可以：
echo 1. 双击运行exe文件
echo 2. 将exe文件复制到其他位置
echo 3. 创建桌面快捷方式
echo 4. 设置开机自启动
echo.

REM 询问是否打开输出目录
set /p OPEN_FOLDER="是否打开输出目录？(y/n): "
if /i "%OPEN_FOLDER%"=="y" (
    explorer ./dist
)

pause 