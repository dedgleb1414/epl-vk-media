code = open("server_template.py", "r", encoding="utf-8").read()
open("server.py", "w", encoding="utf-8").write(code)
print("OK")