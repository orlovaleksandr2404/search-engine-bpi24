#!/bin/bash

echo "Запуск инициализации тестовых данных"

DOWNLOAD_DIR="./temp_lectures"
mkdir -p "$DOWNLOAD_DIR"
cd "$DOWNLOAD_DIR"

# лекции по ML с github (ВШЭ)
URLS=(
    "https://raw.githubusercontent.com/esokolov/ml-course-hse/master/2016-fall/lecture-notes/lecture01-intro.pdf"
    "https://raw.githubusercontent.com/esokolov/ml-course-hse/master/2016-fall/lecture-notes/lecture02-linregr.pdf"
    "https://raw.githubusercontent.com/esokolov/ml-course-hse/master/2016-fall/lecture-notes/lecture03-linregr.pdf"
    "https://raw.githubusercontent.com/esokolov/ml-course-hse/master/2016-fall/lecture-notes/lecture04-linclass.pdf"
    "https://raw.githubusercontent.com/esokolov/ml-course-hse/master/2016-fall/lecture-notes/lecture05-linclass.pdf"
    "https://raw.githubusercontent.com/esokolov/ml-course-hse/master/2016-fall/lecture-notes/lecture06-linclass.pdf"
    "https://raw.githubusercontent.com/esokolov/ml-course-hse/master/2016-fall/lecture-notes/lecture07-trees.pdf"
    "https://raw.githubusercontent.com/esokolov/ml-course-hse/master/2016-fall/lecture-notes/lecture08-ensembles.pdf"
    "https://raw.githubusercontent.com/esokolov/ml-course-hse/master/2016-fall/lecture-notes/lecture09-ensembles.pdf"
    "https://raw.githubusercontent.com/esokolov/ml-course-hse/master/2016-fall/lecture-notes/lecture10-ensembles.pdf"
)

echo "Скачиваем 10 лекций..."
FILE_INDEX=1
for url in "${URLS[@]}"
do
    filename="lecture_$FILE_INDEX.pdf"
    echo "Загрузка файла: $filename"
    curl -s -L -A "Mozilla/5.0" "$url" -o "$filename"
    FILE_INDEX=$((FILE_INDEX + 1))
done

echo "Все файлы успешно скачаны локально"
echo ""
echo "Отправляем файлы в бэкенд на FastAPI..."

API_URL="http://localhost:8000/api/v1/documents/upload"

for file in *.pdf
do
    echo "Отправка $file через POST API..."
    
    HTTP_CODE=$(curl -s -o response_body.json -w "%{http_code}" -X POST "$API_URL" \
      -H "accept: application/json" \
      -H "Content-Type: multipart/form-data" \
      -F "file=@$file;type=application/pdf")
    
    if [ "$HTTP_CODE" -eq 200 ] || [ "$HTTP_CODE" -eq 201 ]; then
        echo "OK: $file успешно обработан сервером (Код: $HTTP_CODE)"
    else
        echo "Ошибка при загрузке $file (Код: $HTTP_CODE)"
        echo "Ответ бэкенда:"
        cat response_body.json
        echo ""
    fi
done

echo ""
echo "Удаление временных файлов и папок..."
rm -f response_body.json
cd ..
rm -rf "$DOWNLOAD_DIR"

echo "Можно открывать http://localhost:3000 и тестировать поиск."
