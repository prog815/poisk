@echo off
chcp 65001 > nul
echo Poisk - Test environment deployment
echo ===================================
echo.

if not exist admin_test_env mkdir admin_test_env

echo Copying files to admin_test_env...
copy generate_search_page.py admin_test_env\ > nul
if exist template.html copy template.html admin_test_env\ > nul 2>&1
if exist styles.css copy styles.css admin_test_env\ > nul 2>&1
if exist search.js copy search.js admin_test_env\ > nul 2>&1
if exist create_distribution.py copy create_distribution.py admin_test_env\ > nul 2>&1
if exist config.ini.template copy config.ini.template admin_test_env\ > nul 2>&1

echo Done. Files copied to admin_test_env\
echo.
echo Note: config.ini is NOT copied (admin settings preserved)
echo.
pause