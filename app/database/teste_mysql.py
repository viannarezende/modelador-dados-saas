import pymysql

conn = pymysql.connect(
    host="15.235.9.101",
    port=3306,
    user="gmfxhxeo_user_modelo_dados",
    password="ri({GH8)udFVw~DU",
    database="Mysql"
)

print("Conectado com sucesso!")

conn.close()