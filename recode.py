
with open('all_data1.json', 'rb') as f:
    data = f.read()

with open('all_data_utf8.json', 'w', encoding='utf-8') as f:
    f.write(data.decode('cp1251', errors='ignore')) 

print("Файл перекодирован в all_data_utf8.json")


