from PyInstaller.utils.hooks import collect_data_files

# This hook tells PyInstaller to find and bundle all non-Python files
# (like the required .js files) from the selenium_stealth package.
datas = collect_data_files('selenium_stealth')