# api dictionary.yandex для перевода текста
import requests
import json
api_key = 'dict.1.1.20210731T121051Z.88235e3a50c76deb.f46658f04a0c5cb93f33e82daafd5ad6f091e9c2'
service = 'https://dictionary.yandex.net/api/v1/dicservice.json/lookup'
languages = 'en-ru'

# текст для перевода
text = 'open'

response = requests.get(f'{service}?key={api_key}&lang={languages}&text={text}')
if response.ok:
    j_response = response.json()
    
    # запись в файл
    with open('translation.json', 'w', encoding='utf-8') as file:
        json.dump(j_response, file, indent=4, ensure_ascii=False)
        
    # вывод перевода
    translation = [x['text'] for x in j_response['def'][0]['tr']]
    print(j_response['def'][0]['text'] + ': ' + ', '.join(translation))
else:
    print('Request fault with code ' + str(response.status_code))
